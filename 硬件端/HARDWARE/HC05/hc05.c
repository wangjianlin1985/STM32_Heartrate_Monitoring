#include "hc05.h"
#include "usart2.h"

//初始化HC05模块
//返回值:0,成功;1,失败.
u8 HC05_Init(void)
{
	u8 retry=10,t;	  		 
	u8 temp=1;
	
	GPIO_InitTypeDef GPIO_InitStructure;
	
	RCC_APB2PeriphClockCmd(RCC_STATE,ENABLE);	//使能PORTA C时钟	
 
	GPIO_InitStructure.GPIO_Pin = STATE_Pin;				 // 端口配置
	GPIO_InitStructure.GPIO_Mode = GPIO_Mode_IPU; 		 //上拉输入
	GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;		 //IO口速度为50MHz
	GPIO_Init(GPIOA, &GPIO_InitStructure);					 //根据设定参数初始化PA4
	 
 
	GPIO_InitStructure.GPIO_Pin = EN_Pin;				 // 端口配置
	GPIO_InitStructure.GPIO_Mode = GPIO_Mode_Out_PP; 		 //推挽输出
	GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;		 //IO口速度为50MHz
	GPIO_Init(GPIOA, &GPIO_InitStructure);					 //根据设定参数初始化PC4

	GPIO_SetBits(GPIOA,EN_Pin);
 	
	
	
	
//	
//	while(retry--)
//	{
//		HC05_EN=1;					//KEY置高,进入AT模式
//		delay_ms(10);
//		u2_printf("AT\r\n");		//发送AT测试指令
//		HC05_EN=0;					//KEY拉低,退出AT模式
//		for(t=0;t<10;t++) 			//最长等待50ms,来接收HC05模块的回应
//		{
//			if(USART2_RX_STA&0X8000)break;
//			delay_ms(5);
//		}		
//		if(USART2_RX_STA&0X8000)	//接收到一次数据了
//		{
//			temp=USART2_RX_STA&0X7FFF;	//得到数据长度
//			USART2_RX_STA=0;			 
//			if(temp==4&&USART2_RX_BUF[0]=='O'&&USART2_RX_BUF[1]=='K')
//			{
//				temp=0;//接收到OK响应
//				break;
//			}
//		}			    		
//	}		    
	if(retry==0)temp=1;	//检测失败
	return temp=0;	 
}	 

//获取ATK-HC05模块的角色
//返回值:0,从机;1,主机;0XFF,获取失败.							  
u8 HC05_Get_Role(void)
{	 		    
	u8 retry=0X0F;
	u8 temp,t;
	while(retry--)
	{
		HC05_EN=1;					//KEY置高,进入AT模式
		delay_ms(10);
		u2_printf("AT+ROLE?\r\n");	//查询角色
		for(t=0;t<20;t++) 			//最长等待200ms,来接收HC05模块的回应
		{
			delay_ms(10);
			if(USART2_RX_STA&0X8000)break;
		}		
		HC05_EN=0;					//KEY拉低,退出AT模式
		if(USART2_RX_STA&0X8000)	//接收到一次数据了
		{
			temp=USART2_RX_STA&0X7FFF;	//得到数据长度
			USART2_RX_STA=0;			 
			if(temp==13&&USART2_RX_BUF[0]=='+')//接收到正确的应答了
			{
				temp=USART2_RX_BUF[6]-'0';//得到主从模式值
				break;
			}
		}		
	}
	if(retry==0)temp=0XFF;//查询失败.
	return temp;
} 			
//ATK-HC05设置命令
//此函数用于设置ATK-HC05,适用于仅返回OK应答的AT指令
//atstr:AT指令串.比如:"AT+RESET"/"AT+UART=9600,0,0"/"AT+ROLE=0"等字符串
//返回值:0,设置成功;其他,设置失败.							  
u8 HC05_Set_Cmd(u8* atstr)
{	 		    
	u8 retry=0X0F;
	u8 temp,t;
	while(retry--)
	{
		HC05_EN=1;					//KEY置高,进入AT模式
		delay_ms(10);
		u2_printf("%s\r\n",atstr);	//发送AT字符串
		HC05_EN=0;					//KEY拉低,退出AT模式
		for(t=0;t<20;t++) 			//最长等待100ms,来接收HC05模块的回应
		{
			if(USART2_RX_STA&0X8000)break;
			delay_ms(5);
		}		
		if(USART2_RX_STA&0X8000)	//接收到一次数据了
		{
			temp=USART2_RX_STA&0X7FFF;	//得到数据长度
			USART2_RX_STA=0;			 
			if(temp==4&&USART2_RX_BUF[0]=='O')//接收到正确的应答了
			{			
				temp=0;
				break;			 
			}
		}		
	}
	if(retry==0)temp=0XFF;//设置失败.
	return temp;
} 