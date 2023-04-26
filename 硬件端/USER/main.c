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

//ALIENTEKminiSTM32��������չʵ�� 
//ATK-HC05��������ģ��ʵ��-�⺯���汾  
//����֧�֣�www.openedv.com
//������������ӿƼ����޹�˾ 
//ALIENTEKս��STM32������ʵ��13
//TFTLCD��ʾʵ��  
//����֧�֣�www.openedv.com
//������������ӿƼ����޹�˾ 
 	
extern int Move_gewei;
extern int Move_shiwei;
extern int Move_baiwei;
extern int Move_qianwei;
extern int Move_wanwei; 


char str[100];

//����
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
//��������
void heart(void);

int main(void)
 {	 
	u8 t;
	u8 key;
	u8 sendmask=0;
	u8 sendcnt=0;
	u8 sendbuf[20];	  
	u8 reclen=0;  
	delay_init();	    	 //��ʱ������ʼ��	  
	NVIC_Configuration(); 	 //����NVIC�жϷ���2:2λ��ռ���ȼ���2λ��Ӧ���ȼ�
	uart_init(9600);	 	//���ڳ�ʼ��Ϊ9600
	USART2_Init(9600);	//��ʼ������2Ϊ:9600,������.
	 
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
		printf("HC05ģ����������\r\n");
   
	}else{
		 printf("HC05ģ���ⲻ����������ģ���뿪��������ӣ�Ȼ��λ���������²��ԡ�\r\n");
		while(1);
	}
	
		/*1. ��ʼ��HC05��������*/
		printf("1 �������ڳ�ʼ��.........\r\n");

		while(HC05_Init()){}
		
//		/*���õ�ǰ����Ϊ�ӻ�ģʽ*/
		HC05_Set_Cmd("AT+ROLE=0"); //����Ϊ�ӻ�ģʽ
		if(HC05_Get_Role()==0)printf("��ǰ�������ڴӻ�״̬!\r\n");
		else if(HC05_Get_Role()==1)printf("��ǰ������������״̬!\r\n");
		HC05_Set_Cmd("AT+RESET\r\n");	//��λATK-HC05ģ��
		delay_ms(2000);			//�ȴ�����ģ���ȶ�
			
		/*2. ��ѯ��������״̬*/
		if(HC05_Get_Role()==0)printf("2 ��ǰ�������ڴӻ�״̬!\r\n");
		else if(HC05_Get_Role()==1)printf("2 ��ǰ������������״̬!\r\n");
		else printf("2 ��ǰ��������״̬��ѯʧ��!\r\n");
	
		/*3. �鿴��������״̬*/
		if(HC05_STATE==1)printf("3 ��ǰ�������ӳɹ�!\r\n");
		else printf("3 ��ǰ����δ����!\r\n");
		
		/*4. ��������������*/
		if(HC05_Set_Cmd("AT+NAMEHC-05"))printf("4 ������������ʧ��!\r\n");
		else printf("4 ������������Ϊ HC-05 \r\n");
		
		/*5. ���������������*/
		if(HC05_Set_Cmd("AT+PSWD=8888"))printf("5 ���������������ʧ��!\r\n"); //���������4λ
		else printf("5 ���������������Ϊ 1234 \r\n");
		
		
		//if(HC05_Bluetooth_SetCmd("AT+UART=921600,0,0\r\n"))printf("5 �������������óɹ�!\r\n"); //���������4λ
		//else printf("5 ��������������ʧ��!\r\n\r\n");
		
		/*6. �ȴ���������*/
		printf("�ȴ���������.....\r\n");
		while(!HC05_STATE){}
		printf("��ǰ�������ӳɹ�! ���뵽����͸��ģʽ\r\n");

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
	  
		if(USART2_RX_STA&0X8000)			//���յ�һ��������
		{
			//LCD_Fill(30,200,240,320,WHITE);	//�����ʾ
 			reclen=USART2_RX_STA&0X7FFF;	//�õ����ݳ���
		  	USART2_RX_BUF[reclen]=0;	 	//���������
			if(reclen==9||reclen==8) 		//����DS1���
			{
//				if(strcmp((const char*)USART2_RX_BUF,"+LED1 ON")==0)LED1=0;	//��LED1
//				if(strcmp((const char*)USART2_RX_BUF,"+LED1 OFF")==0)LED1=1;//�ر�LED1
			}
 			//LCD_ShowString(30,200,209,119,16,USART2_RX_BUF);//��ʾ���յ�������
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
