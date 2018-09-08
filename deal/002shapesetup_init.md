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

包括shft_enable、bend_enable、操作工弯辊补偿、窜辊初始位置。

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



bnd_enab如果为true，且为CVC辊形，则pcFSStdDloc->force_bnd为nom弯辊力减去flt_vrn，如果为大凹辊或其它辊形，则不减去flt_vrn。如果bnd_enab为false，则直接继承psSSys->force_bnd[ passIdx ]，并用pcFSStdDloc->pcFSStd->force_bnd_lim限幅。如果被限幅了，说明弯辊力超出硬极限，报错并报红。



窜辊初始位置的选择，中间变量为wr_shft_local

如果刚刚换过辊，则锁着窜辊帮助前期开轧过渡的调平控制。窜辊设定为0。如果wrshftsel_init_at_cur或wrshftsel_find_opt，则初始窜辊位置采用psSSys->pos_shft[ passIdx ]。因此要引入psSSys->pos_shft这个是怎么算的。

之后对wr_shft_local限幅获得pcFSPassD->pcFSStdD[ iter ]->wr_shft。wr_shft不能超限幅，否则出现硬限幅的警告。

```c
                        pcFSPassD->pcFSStdD[ iter ]->wr_shft = 
                            cMathUty::Clamp( wr_shft_local,
                                             pcFSStdDloc->pcFSStd->wr_shft_lim[ minl ],
                                             pcFSStdDloc->pcFSStd->wr_shft_lim[ maxl ] );
```

=====================================================

窜辊初始位置的选择  select the initial shifting在这段代码中要这么理解。

首先设定一个level_std来表示开轧后是否以调平为主的指示器。这个参数由于num_coils_to_lvl被设定为-1，因此level_std的值永远为false。

其次wr_shft_local为窜辊的中间计算结果变量。wr_shft_local仅用做状态值的·存储，最终是要确定pcFSStdDloc->wr_shft的值。pcFSStdDloc为FSStd动态对象的局部指针引用。

之后分两种情况考虑，一种是此道次非空过，窜辊可以用。另一种是此道次空过或窜辊不能用。

在此道次非空过，窜辊可以用的情况下，再分两种情况，一种是CVC，一种是非CVC。非CVC情况下好办wr_shft的值直接由psSSys->targ_pos_shft赋值。CVC情况下要考虑wr_shft_use的取值，默认情况下wr_shft_use取值为wrshftsel_init_at_cur，wr_shft初始值由psSSys->pos_shft赋值并用wr_shft_lim限幅，若操作工锁窜辊wr_shft初始值直接设为0。

此道次空过或窜辊不能用时，wr_shft初始值由psSSys->pos_shft赋值并用wr_shft_lim限幅。

从日志情况来看fsstd的wr_shft初始值一般就是为0。

=====================================================

之后为窜辊软极限和弯辊极限的计算。（682行到919行）

窜辊软极限计算（680-837行）

分两种情况考虑。CVC和非CVC。（空过直接包含在条件中）

如果是非CVC辊形，则直接赋值，根据赋值链，wr_shft_lim值来自psSSys->targ_pos_shft。

如果是CVC辊形，窜辊被锁（包括开轧后的调平锁定）或此道次空过pcFSStdDloc->wr_shft_lim直接赋值为pcFSStdDloc->wr_shft初始值。如果窜辊没有被锁，则计算窜辊软极限。

窜辊软极限的计算我仔细看了一下，实际上就是为last_pos_shft加上或减去max_shft，如果轧辊磨损严重，就将max_shft换成bad_wear_max_shft。

ssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssss

首先进行bad_wear_check

之后计算最大窜辊量dlt_shft，窜辊软极限的上下限主要受dlt_shft控制。中间线由wr_shft控制。

pcFSStdDloc->wr_shft_lim由pcFSStdDloc->pcFSStd->wr_shft_lim限幅确定，增益为psSPRP->min_accu_lmt。

如果是非CVC，则直接使用窜辊初始位置wr_shft。

==========================================

粗轧中间坯凸度计算初始化（977-1063）

粗轧中间坯凸度由use_rmx_prf决定是否使用rmx的中间坯凸度，还是通过插值重新计算一个粗轧中间坯凸度。

第一道次的前一个对象，即中间坯对象pcFstFSPassD->previous_obj，其相应的pcAlcLPceD和pcEvlLPceD的prf和ef_pu_prf就是之前计算的粗轧中间坯凸度和单位凸度。



包络线的中间坯凸度也进行了赋值。

​```c
        for ( int i = minl; i <= maxl; i++ )
        {
            pcFSPassD->pcVecPEnvD[ iter ]->pu_prf_env[ i ]    =
                pu_prf_pass0;
            pcFSPassD->pcVecPEnvD[ iter ]->ef_pu_prf_env[ i ] =
                pu_prf_pass0;
        }
​```
pcTargtD->en_pu_prf 也是直接由 pu_prf_pass0赋值。

​```c
pcTargtD->en_pu_prf = pu_prf_pass0;
​```



F7或最后一个机架的弯辊力极限需要补偿平直度自学习的值。

​```c
					pcLstActFSPassD->pcFSStdD[ iter ]->force_bnd_lim[ i ] =
						pcLstActFSPassD->pcFSStdD[ iter ]->force_bnd_lim[ i ] -
	
						//psSAMP->flt_vrn;
						//0.0F;
						psSAMP->flt_vrn;
​```


~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~