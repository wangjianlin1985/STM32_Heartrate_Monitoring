#ifndef __LED_H
#define __LED_H
#include "sys.h"
//LED �˿ڶ���
#define LED0 PAout(8) // PA8

#define LED1 PDout(2) // PD2

#define DS0_OPEN  GPIO_ResetBits(GPIOA, GPIO_Pin_8);//DS0��

#define DS0_CLOSE GPIO_SetBits(GPIOA, GPIO_Pin_8);//DS0��

#define DS1_OPEN  GPIO_ResetBits(GPIOD, GPIO_Pin_2);//DS1��

#define DS1_CLOSE GPIO_SetBits(GPIOD, GPIO_Pin_2);//DS1��

void LED_Init(void);//��ʼ��
#endif
