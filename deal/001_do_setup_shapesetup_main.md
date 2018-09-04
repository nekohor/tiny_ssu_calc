# 克隆原型记录和说明

proddispatch.cxx代码中Receive_Work函数从开始进行各种参数的导入和状态检查。

2250产线到681行到1030行进行scf窜辊相关计算。1580则没有。

Do setup开始进行真正的设定计算，1580产线Do setup在832行，2250产线Do setup在1187行.

## Do setup

检查RB bleedoff counter是否大于1，是的话用samp table代替ssys record，否则继续沿用ssys record。这段一般注释掉。

```C
		// Check to see if RB bleedoff counter is greater then 1. 
		// If so then use sAMP table to replace sSys record value,
		// and use this value, else keep using the sSys value.
		//for (int i = 0; i < max_passes_fm; i++ )
		//{
		//if ( pcSched->pcFSSched->pcSAMP->state.bnd_ofs_counter[i] > 1)
		//{
		//  pcSched->pcFSSched->pcSSys->state.op_bnd_of[i] =
		//  pcSched->pcFSSched->pcSAMP->state.bending_ofs[i];
		//}
		//}
```

redrft_perm的设定，在实际过程中一般为false，不给干预轧制力的分配。

sup_time设定，在原型计算中不用管。

pcShapeSetupD->Main()是为板形设定计算的主函数。2250产线比1580产线多一个iter_count，见下面第三个参数。

```c
	pcSched->pcFSSched->pcShapeSetupD->
		Main( use_roll_proj,
		redrft_perm,

             0,

		pcSched);
```
由于redrft_perm一般为false，因此不会触发板形模型的重计算，下面代码不要管。

```c
	if ( redrft_perm && !pcSched->pcFSSched->pcShapeSetupD->ok )
	{
		redrft_perm = false;
		pcSched->pcFSSched->pcShapeSetupD->redrfted = false;
		pcSched->pcFSSched->pcShapeSetupD->Main( use_roll_proj,
			redrft_perm,
			pcSched );
	}
```
接下来时一堆XXX_ok和红黄绿灯状态处理，注意时状态处理。



接下来各种COPY表链工作

1. Copy references to external records



@@Check and reset floating point exception status, in case it has been set somewhere.

@@Copy SSU references, process transfer functions / gains and other miscellaneous.

@@Send data to the reply handle   pcSched->pcSetupD->Send_Reply()

@@Logging



2. Copy SSU references, process transfer functions / gains and other

之后send reply和logging相关代码



## pcShapeSetupD->Main()

Main()的调用1580产线在873行。



最基础的两个指针以及各种状态设定。

    MDSVERIFYNAME( pcSched, "pcSched" );
    MDSVERIFYNAME( pcSched->pcFSSched, "pcSched->pcFSSched" );
```c
//------------------------------------------------------------------
// Initialize the SSU model status indicator to "RED" and validity
// indicator to FALSE.
//------------------------------------------------------------------
this->status = cMdlparam::cs_red;
this->ok     = false;
```


Main()中的第一个大函数时初始化静态参数的函数Initialize_Static_Objects，在其中将pcPassD道次对象复制到pcFSPassD。接着调用Copy_Object_Chain将pcPassD当中的和FSU有关的参数如咬入、出口带钢等复制到pcFSPassD。



从头到尾循环道次对象找到最后一个活跃的道次对象，一般为F7。

```c
        // -------------------------------------
        // Loop thru all Pass objects and find
        // Last Active Pass Pointer
        // -------------------------------------
```





1580产线1110行 2250产线XXXX行，change判断标识的声明和赋值。

```c
        this->family_chg         = false;
        this->narrow_to_wide_chg = false;
        this->wide_to_narrow_chg = false;
        this->prd_chg            = false;
//@GSM(E-01) start
#if GSM_RB_OFS_BLEEDOFF
        this->lot_chg            = false;
```



如果换辊或其它条件发生，则清空重置（reset）自学习。

```c
        bool update =pcSched->pcFSSched->pcSAMP->Reset_Verniers (
              pcObjChain->Head_Index(),
              pcShapeSetup->num_std_chg_lim,
              pcShapeSetup->reset_bleedoff_lot,
              pcSched->pcSupPassD[ 1 ],
              pcSched->pcSupPassD[ pcSched->pcMap->pcMapPassTbl->num_passes - 1 ],
              this->family_chg,
              this->narrow_to_wide_chg,
              this->wide_to_narrow_chg,
              this->lot_chg);
```

注意板形自学习的更新在cource2之后。

```
        // Update the SAMP model tables only if mode is not in simulation and
        // reset verniers made a change and
        // after course-2
        if (update &&
            !pcSched->pcFSSched->pcSSys->state.sim_mode &&
            pcSched->wrk[cXlevt::wrk_course2] >= 1)
//@2ND-2(MAT037) end
        {
            //----------------------------------------------------
            // Return the SAMP model tabel to the models database.
            //----------------------------------------------------
            if ( !pcSched->pcFSSched->pcSAMP->Put_Table( 1,
                               &pcSched->pcFSSched->pcSAMP->state ) )
            {
                EMSG << "Error returning SAMP model table for vernier zeroing"
                     << END_OF_MESSAGE;
                return;
            }
```



最终调用Init（）和Reference（）进行初始化和设定计算。