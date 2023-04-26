#include "led.h"
#include "delay.h"
#include "sys.h"
#include "usart.h"

#include "hc05.h"
#include "usart2.h"			 	 
#include "string.h"	 
#include "bsp_exti.h"
#include "max30102.h" 
#include "myiic.h"
#include "algorithm.h"

//ALIENTEKminiSTM32开发板扩展实验 
//ATK-HC05蓝牙串口模块实验-库函数版本  
//技术支持：www.openedv.com
//广州市星翼电子科技有限公司 
//ALIENTEK战舰STM32开发板实验13
//TFTLCD显示实验  
//技术支持：www.openedv.com
//广州市星翼电子科技有限公司 
 	
extern int Move_gewei;
extern int Move_shiwei;
extern int Move_baiwei;
extern int Move_qianwei;
extern int Move_wanwei; 


char str[100];

//心率
uint32_t aun_ir_buffer[500]; //IR LED sensor data
int32_t n_ir_buffer_length;    //data length
uint32_t aun_red_buffer[500];    //Red LED sensor data
int32_t n_sp02; //SPO2 value
int8_t ch_spo2_valid;   //indicator to show if the SP02 calculation is valid
int32_t n_heart_rate;   //heart rate value
int8_t  ch_hr_valid;    //indicator to show if the heart rate calculation is valid
uint8_t uch_dummy;
uint32_t un_min, un_max, un_prev_data;  
int i;
int32_t n_brightness;
float f_temp;
u8 temp_num=0;
u8 temp[6];
u8 dis_hr=0,dis_spo2=0;
int time;	
uint8_t hc05_role=0; 

#define MAX_BRIGHTNESS 255
//函数声明
void heart(void);

int main(void)
 {	 
	u8 t;
	u8 key;
	u8 sendmask=0;
	u8 sendcnt=0;
	u8 sendbuf[20];	  
	u8 reclen=0;  
	delay_init();	    	 //延时函数初始化	  
	NVIC_Configuration(); 	 //设置NVIC中断分组2:2位抢占优先级，2位响应优先级
	uart_init(9600);	 	//串口初始化为9600
	USART2_Init(9600);	//初始化串口2为:9600,波特率.
	 
	EXTI_Key_Config ();
	 
	max30102_init();
  printf("\r\n MAX30102  init  \r\n");	 
   delay_ms(1500);
	//POINT_COLOR=RED;
	printf("ALIENTEK STM32 ^_^\r\n");	
	printf("HC05 BLUETOOTH COM TEST\r\n");	
	printf("ATOM@ALIENTEK\r\n");
	if(HC05_Init() ==0)
	{
		printf("HC05模块检测正常。\r\n");
   
	}else{
		 printf("HC05模块检测不正常，请检查模块与开发板的连接，然后复位开发板重新测试。\r\n");
		while(1);
	}
	
		/*1. 初始化HC05串口蓝牙*/
		printf("1 蓝牙正在初始化.........\r\n");

		while(HC05_Init()){}
		
//		/*设置当前蓝牙为从机模式*/
		HC05_Set_Cmd("AT+ROLE=0"); //设置为从机模式
		if(HC05_Get_Role()==0)printf("当前蓝牙处于从机状态!\r\n");
		else if(HC05_Get_Role()==1)printf("当前蓝牙处于主机状态!\r\n");
		HC05_Set_Cmd("AT+RESET\r\n");	//复位ATK-HC05模块
		delay_ms(2000);			//等待蓝牙模块稳定
			
		/*2. 查询蓝牙主从状态*/
		if(HC05_Get_Role()==0)printf("2 当前蓝牙处于从机状态!\r\n");
		else if(HC05_Get_Role()==1)printf("2 当前蓝牙处于主机状态!\r\n");
		else printf("2 当前蓝牙主从状态查询失败!\r\n");
	
		/*3. 查看蓝牙连接状态*/
		if(HC05_STATE==1)printf("3 当前蓝牙连接成功!\r\n");
		else printf("3 当前蓝牙未连接!\r\n");
		
		/*4. 设置蓝牙的名称*/
		if(HC05_Set_Cmd("AT+NAMEHC-05"))printf("4 蓝牙名称设置失败!\r\n");
		else printf("4 蓝牙名称设置为 HC-05 \r\n");
		
		/*5. 设置蓝牙配对密码*/
		if(HC05_Set_Cmd("AT+PSWD=8888"))printf("5 蓝牙配对密码设置失败!\r\n"); //密码必须是4位
		else printf("5 蓝牙配对密码设置为 1234 \r\n");
		
		
		//if(HC05_Bluetooth_SetCmd("AT+UART=921600,0,0\r\n"))printf("5 蓝牙波特率设置成功!\r\n"); //密码必须是4位
		//else printf("5 蓝牙波特率设置失败!\r\n\r\n");
		
		/*6. 等待蓝牙连接*/
		printf("等待蓝牙连接.....\r\n");
		while(!HC05_STATE){}
		printf("当前蓝牙连接成功! 进入到数据透传模式\r\n");

	un_min=0x3FFFF;
	un_max=0;
	n_ir_buffer_length=500; //buffer length of 100 stores 5 seconds of samples running at 100sps
	//read the first 500 samples, and determine the signal range
    for(i=0;i<n_ir_buffer_length;i++)
    {
        while(MAX30102_INT==1);   //wait until the interrupt pin asserts
        
		max30102_FIFO_ReadBytes(REG_FIFO_DATA,temp);
		aun_red_buffer[i] =  (long)((long)((long)temp[0]&0x03)<<16) | (long)temp[1]<<8 | (long)temp[2];    // Combine values to get the actual number
		aun_ir_buffer[i] = (long)((long)((long)temp[3] & 0x03)<<16) |(long)temp[4]<<8 | (long)temp[5];   // Combine values to get the actual number
            
        if(un_min>aun_red_buffer[i])
            un_min=aun_red_buffer[i];    //update signal min
        if(un_max<aun_red_buffer[i])
            un_max=aun_red_buffer[i];    //update signal max
    }
	un_prev_data=aun_red_buffer[i];
	//calculate heart rate and SpO2 after first 500 samples (first 5 seconds of samples)
    maxim_heart_rate_and_oxygen_saturation(aun_ir_buffer, n_ir_buffer_length, aun_red_buffer, &n_sp02, &ch_spo2_valid, &n_heart_rate, &ch_hr_valid);
 	while(1) 
	{	
			
			heart ();
			delay_ms(2000);
	  
		if(USART2_RX_STA&0X8000)			//接收到一次数据了
		{
			//LCD_Fill(30,200,240,320,WHITE);	//清除显示
 			reclen=USART2_RX_STA&0X7FFF;	//得到数据长度
		  	USART2_RX_BUF[reclen]=0;	 	//加入结束符
			if(reclen==9||reclen==8) 		//控制DS1检测
			{
//				if(strcmp((const char*)USART2_RX_BUF,"+LED1 ON")==0)LED1=0;	//打开LED1
//				if(strcmp((const char*)USART2_RX_BUF,"+LED1 OFF")==0)LED1=1;//关闭LED1
			}
 			//LCD_ShowString(30,200,209,119,16,USART2_RX_BUF);//显示接收到的数据
 			USART2_RX_STA=0;	 
		}	 															     				   
			
	}											    
}
 
void heart(void)
{
	 i=0;
        un_min=0x3FFFF;
        un_max=0;
		
		//dumping the first 100 sets of samples in the memory and shift the last 400 sets of samples to the top
        for(i=100;i<500;i++)
        {
            aun_red_buffer[i-100]=aun_red_buffer[i];
            aun_ir_buffer[i-100]=aun_ir_buffer[i];
            
            //update the signal min and max
            if(un_min>aun_red_buffer[i])
            un_min=aun_red_buffer[i];
            if(un_max<aun_red_buffer[i])
            un_max=aun_red_buffer[i];
        }
		//take 100 sets of samples before calculating the heart rate.
        for(i=400;i<600;i++)
        {
            un_prev_data=aun_red_buffer[i-1];
            while(MAX30102_INT==1);
            max30102_FIFO_ReadBytes(REG_FIFO_DATA,temp);
			aun_red_buffer[i] =  (long)((long)((long)temp[0]&0x03)<<16) | (long)temp[1]<<8 | (long)temp[2];    // Combine values to get the actual number
			aun_ir_buffer[i] = (long)((long)((long)temp[3] & 0x03)<<16) |(long)temp[4]<<8 | (long)temp[5];   // Combine values to get the actual number
        
            if(aun_red_buffer[i]>un_prev_data)
            {
                f_temp=aun_red_buffer[i]-un_prev_data;
                f_temp/=(un_max-un_min);
                f_temp*=MAX_BRIGHTNESS;
                n_brightness-=(int)f_temp;
                if(n_brightness<0)
                    n_brightness=0;
            }
            else
            {
                f_temp=un_prev_data-aun_red_buffer[i];
                f_temp/=(un_max-un_min);
                f_temp*=MAX_BRIGHTNESS;
                n_brightness+=(int)f_temp;
                if(n_brightness>MAX_BRIGHTNESS)
                    n_brightness=MAX_BRIGHTNESS;
            }
			//send samples and calculation result to terminal program through UART
			if(ch_hr_valid == 1 && ch_spo2_valid ==1)//**/ ch_hr_valid == 1 && ch_spo2_valid ==1 && n_heart_rate<120 && n_sp02<101
			{
				dis_hr = n_heart_rate;
				dis_spo2 = n_sp02;
			}
			else
			{
				dis_hr = 0;
				dis_spo2 = 0;
			}

		}
			if(dis_hr == 0 && dis_spo2 == 0)  //**dis_hr == 0 && dis_spo2 == 0
			{
				sprintf((char *)str,"HR:--- SpO2:--- ");//**HR:--- SpO2:---
				printf("HR:--- SpO2:--- Move:%d%d%d%d%d \r\n ",Move_wanwei,Move_qianwei,Move_baiwei,Move_shiwei,Move_gewei);		
			
			}
			else{
				sprintf((char *)str,"HR:%3d SpO2:%3d ",dis_hr,dis_spo2);//**HR:%3d SpO2:%3d 
				printf("HR:%3d SpO2:%3d Move:%d%d%d%d%d \r\n ",dis_hr,dis_spo2,Move_wanwei,Move_qianwei,Move_baiwei,Move_shiwei,Move_gewei);
				sprintf(str,"%d-%d-%d%d%d%d%d ",dis_hr,dis_spo2,Move_wanwei,Move_qianwei,Move_baiwei,Move_shiwei,Move_gewei);
				u2_printf(str);
			
			}
       maxim_heart_rate_and_oxygen_saturation(aun_ir_buffer, n_ir_buffer_length, aun_red_buffer, &n_sp02, &ch_spo2_valid, &n_heart_rate, &ch_hr_valid);
		
			
			
				

}
