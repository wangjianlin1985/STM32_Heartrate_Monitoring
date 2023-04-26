#ifndef __HC05_H
#define __HC05_H

#include "sys.h"

//连接模块GPIO相关参数的一层封装
//**********************************************************************************
#define RCC_STATE  RCC_APB2Periph_GPIOA

#define STATE_Pin GPIO_Pin_5 
#define EN_Pin GPIO_Pin_7
//**********************************************************************************
#define HC05_STATE  	PAin(5)		//蓝牙连接状态信号
#define HC05_EN  	    PAout(7) 	//蓝牙控制EN信号



u8 HC05_Init(void);
//void HC05_CFG_CMD(u8 *str);
u8 HC05_Get_Role(void);
u8 HC05_Set_Cmd(u8* atstr);	
#endif