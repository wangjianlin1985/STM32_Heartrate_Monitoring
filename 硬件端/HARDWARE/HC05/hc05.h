#ifndef __HC05_H
#define __HC05_H

#include "sys.h"

//����ģ��GPIO��ز�����һ���װ
//**********************************************************************************
#define RCC_STATE  RCC_APB2Periph_GPIOA

#define STATE_Pin GPIO_Pin_5 
#define EN_Pin GPIO_Pin_7
//**********************************************************************************
#define HC05_STATE  	PAin(5)		//��������״̬�ź�
#define HC05_EN  	    PAout(7) 	//��������EN�ź�



u8 HC05_Init(void);
//void HC05_CFG_CMD(u8 *str);
u8 HC05_Get_Role(void);
u8 HC05_Set_Cmd(u8* atstr);	
#endif