from langchain.llms import OpenAI   
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import json
from pydantic import BaseModel
from LLM_PublicHouseAllocation.manager import TenantManager,HouseManager
from LLM_PublicHouseAllocation.involvers import System
from typing import Optional
import re
import asyncio
from LLM_PublicHouseAllocation.llms import APIKeyPool
from tqdm import tqdm
import random
class Global_Score(BaseModel):
    tenant_manager:Optional[TenantManager]=None
    system:Optional[System]=None
    save_dir:str=""
    result:dict={}
    llm_pool:Optional[APIKeyPool]=None
    
    
    def __init__(self,**kargs) -> None:
        super().__init__(**kargs)
        self.rate()
        self.save()

    
    @classmethod
    def initialization(
        cls,
        tenant_manager:TenantManager,
        system:System,
        save_dir:str,
        llm_pool:APIKeyPool
    ):
        import os
        if os.path.exists(save_dir):
            with open(save_dir,'r',encoding = 'utf-8') as f:
                result=json.load(f)
        return cls(
            tenant_manager=tenant_manager,
            system=system,
            save_dir=save_dir,
            result=result,
            llm_pool =llm_pool
        )
    
    
    def chain(self,llm):
        template="""
            {role_description}\
            {house_info}
            
            
Here's some important background information:

1. The average living area of these houses is around 20 square meters. If the average living area exceeds 20 for you, the house should be relatively spacious, while if it's less than 20, it would be rather cramped.
2. For this pool of houses: the price range is roughly between 900 and 2600, and the house area is approximately 35-65 square meters. Please keep this distribution in mind and evaluate the value of the house relative to this pool of houses.
3. Please remember your persona and make evaluations of the houses that align with that persona.
4. Try to distribute your ratings evenly.


Please rate based on the information and properties of the house. Score the house from 1-10, with a higher score indicating the house better meets your requirements.
             
            1 point: The condition of the house is extremely poor, with multiple serious problems, such as structural instability, aging or severe damage to facilities, and it is basically unfit for habitation.

            2 points: The home has obvious flaws and issues, such as an old electrical system, leaks, or broken fixtures that require extensive repairs and updates.

            3 points: The basic functions of the house are acceptable, but there are still many inconveniences, such as aging facilities, many minor repairs, and low comfort.

            4 points: Although the home maintains basic functions, it may lack some comfort or modern facilities, or it may need some repairs and improvements.

            5 points: the house is basically maintained, there are many minor problems, which may affect the daily life of the residents, but overall it is still acceptable.

            6 points: The house is in acceptable condition, with basic functions complete and few minor problems, but it may lack some modern facilities or design.

            7 points: The home is in good condition, features are relatively new, well maintained and may only need minor improvements or updates.

            8 points: The house is in very good condition, with modern facilities and good maintenance, providing a comfortable and convenient living environment.

            9 points: The house is almost perfect, has advanced facilities, elegant design, is well maintained and needs almost no improvements.

            10 points: The house is in immaculate condition, has advanced facilities, is elegantly designed, and is well maintained, providing a living experience that exceeds expectations.
            Please rate this house and explain why. 
            
            {example}
            
            -The required results must conform to the following format of output results:

            Score: Indicates the scoring result, which must be an integer number. 
            Reason: Give reasons why you gave this score

            Return using JSON format.
        """  
        input_variables=["role_description","house_info","example"]
        prompt = PromptTemplate(  
            input_variables=input_variables,  
            template=template,  
        )
        
        return LLMChain(
            llm=llm, prompt=prompt
        )
        
        
        
    def rate(self):
        tenant_ids = list(self.tenant_manager.total_tenant_datas.keys())
        group_size = 10
        group_id = 0
        while(group_id*group_size<len(tenant_ids)):
            stop_id = group_size*(group_id+1)
            stop_id = -1 if len(tenant_ids) ==stop_id else stop_id
            asyncio.run(self.rate_score(tenant_ids[int(group_id*group_size):stop_id]))            
            group_id+=1

    
    
    async def rate_score(self,tenant_ids):
        
        async def rate_one_tenant(tenant_id):
            tenant = self.tenant_manager.total_tenant_datas[tenant_id]
            llm = self.llm_pool.get_llm_single()
            llm_chain = self.chain(llm)
            if tenant_id not in self.result.keys():
                self.result[tenant_id]={}
            
            for house_id in self.system.house_manager.data.keys():
                
                example_template = """
Here's one example:

Score: {score}
Reason: {reason}

End of example                
"""
                
                example = random.sample(list(self.result.values()),1)[0] # 随机采样一个样本
                
                input={
                    "role_description":tenant.get_role_description(),
                    "house_info":self.system.get_score_house_description(house_id,tenant),
                    "example":example_template.format_map(example)
                }
                if self.result[tenant_id].get(house_id,{}).get("score",0) ==0:
                    rated = False
                else:
                    rated = True
                    
                while (not rated):
                    response = await llm_chain.arun(input)
                    response = response.replace("\n","").strip().lower()
                    score_match = re.search(r'score:\s*(\d+)', response)
                    reason_match = re.search(r'reason:\s*(.+)', response)
                    if score_match and reason_match:
                        # 从匹配对象中提取值
                        score = score_match.group(1)
                        reason = reason_match.group(1)
                        # 创建结果字典
                        result_dict = {
                            "score": int(score),
                            "reason": reason
                        }
                        self.result[tenant_id].update({house_id:result_dict})
                    else:
                        try:
                            result = json.loads(response)
                            self.result[tenant_id].update({house_id:result})
                            rated = True
                            break
                        except json.JSONDecodeError as e:
                            print(f"Invalid JSON: {e}")   
                            # self.result[tenant_id].update({house_id:{"score": 0, "reason": ""}})
                            
            
            print(f"tenant {tenant.id} finished rating.")            
            
        await asyncio.gather(*[rate_one_tenant(tenant_id) for tenant_id in tqdm(tenant_ids,desc="Rating the score of houses.")])
            
            
        
            
    def save(self):
        with open(self.save_dir, 'w', encoding='utf-8') as file:
            json.dump(self.result, file, indent=4,separators=(',', ':'),ensure_ascii=False)


    def get_result(self):
        return self.result
     
