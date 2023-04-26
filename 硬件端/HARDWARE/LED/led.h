#ifndef __LED_H
#define __LED_H
#include "sys.h"
//LED 端口定义
#define LED0 PAout(8) // PA8

#define LED1 PDout(2) // PD2

#define DS0_OPEN  GPIO_ResetBits(GPIOA, GPIO_Pin_8);//DS0亮

#define DS0_CLOSE GPIO_SetBits(GPIOA, GPIO_Pin_8);//DS0灭

#define DS1_OPEN  GPIO_ResetBits(GPIOD, GPIO_Pin_2);//DS1亮

#define DS1_CLOSE GPIO_SetBits(GPIOD, GPIO_Pin_2);//DS1灭

void LED_Init(void);//初始化
#endif
