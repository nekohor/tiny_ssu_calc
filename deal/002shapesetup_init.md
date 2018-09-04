# Shapesetup::Init()

cShapeSetupD::Init实际上是在ShapeSetup_req.cxx中。

在这个函数中几个比较重要的对象如下所示。

```c
    MDSVERIFYNAME( psSSys,           "psSSys" );
    MDSVERIFYNAME( psSAMP,           "psSAMP" );
    MDSVERIFYNAME( psSLFG,           "psSLFG" );
    MDSVERIFYNAME( pcFstFSPassD,     "pcFstFSPassD" );
    MDSVERIFYNAME( pcLstFSPassD,     "pcLstFSPassD" );
    MDSVERIFYNAME( pcLstActFSPassD,  "pcLstActFSPassD" );
    MDSVERIFYNAME( pcTargtD,         "pcTargtD" );
```



首先设定PCE的凸度个平直度目标。

```c
        //----------------------------------------------
        // Initialize the static PCE with the following:
        //     Target profile
        //     Target flatness
        //----------------------------------------------
        pcFstFSPassD->pcFSStdD[ iter ]->pcEnPceD->pcPce->tgt_profile  =
            psPDI->tgt_profile + psSSys->op_prf_off;

        pcFstFSPassD->pcFSStdD[ iter ]->pcEnPceD->pcPce->tgt_flatness =
            psPDI->tgt_flatness + psSSys->op_flt_off;
```

注意目标值考虑了操作工的凸度和平直度补偿。



接下来是长短期自学习的处理。
凸度自学习方面，以RM为例，RM凸度自学习的中间变量为prf_vrn_rm_tmp

SLFG考虑的话，首先将psSLFG->prf_vrn_rm赋值给prf_vrn_rm_tmp，之后若在同一个轧制计划中（没有roll_change），出现钢种和规格的跳变，则prf_vrn_rm_tmp加上上一卷增益后的凸度自学习psSAMP->prf_vrn_rm_prev。

这里有一个问题，加上上一卷增益后的凸度自学习之后，prf_vrn_rm_tmp又被重新赋值为当前轧制卷的psSAMP->prf_vrn_rm，再加上轧制卷的psSLFG->prf_vrn_rm。钢种和规格跳变的自学习调整被覆盖掉了。

平直度自学习是加上上一卷增益后的平直度自学习psSAMP->flt_vrn_prev。



自学习初始化完毕后，调用目标对象的初始化。pcTargtD->Init()



## 初始化大循环

目标对象初始化完后，接着是一个F1到F7的大循环，大循环中对每个道次机架的一些动静态参数进行初始化处理。

注意这里有一个局部指针pcFSStdDloc。表示循环中的pcFSStdD所指向的对象。

```c
pcFSStdDloc = pcFSPassD->pcFSStdD[ iter ];
```



ufd_mult和force_bnd_nom的录入



咬入计算中Calculate_DForce_DEnthick和Calculate_DForce_DExthick



初始化动态UFD对象



初始化CRLC对象。wr_crn_off_adj从这里介入。



初始化LRG对象。



初始化LPCE对象。



初始化动态STD对象。

```c
            //-----------------------------------------------------------------
            // Initialize the following dynamic STD quantities:
            //     Roll shifting system enabled indicator
            //     Roll bending system enabled indicator
            //     Operator roll bending force offset =
            //         current operator roll bending force offset
            //     Roll bending force =
            //         nominal roll bending force
            //         if not enabled, operator roll bending force
            //     Roll shift/angle =
            //         current roll shift postion if not shiftable
            //         schedule free reference if parabolic roll crown
            //         controlled by wrshftsel enumeration in calling argument
            //-----------------------------------------------------------------
```

包括shft_enable、bend_enable、操作工弯辊补偿、窜辊位置。

shft_enable、bend_enable没什么好讲的。

注意操作工弯辊补偿当中需要加上短期弯辊自学习补偿psSAMP->bending_ofs。也就是说op_bnd_off当中既包括操作工直接补偿，也包括短期的弯辊自学习补偿。

```c
            pcFSStdDloc->op_bnd_off = psSSys->op_bnd_of[ passIdx ];
//@GSM(E-01) start
#if GSM_RB_OFS_BLEEDOFF
            pcFSStdDloc->op_bnd_off += psSAMP->bending_ofs[ passIdx ];
#endif
//@GSM(E-01) end
```



bnd_enab如果为true，且为CVC辊形，则pcFSStdDloc->force_bnd为nom弯辊力减去flt_vrn，如果为大凹辊或其它辊形，则不减去flt_vrn。

