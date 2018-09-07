# cShapeSetupD::References()

LPce  Update

cLRG Update





cPEnvD::Calculate

cAlcD::Calculate

```c
//@GSM(E-01) start
#if !GSM_RB_OFS_BLEEDOFF
            force_bnd =
                pcFSPassD->pcFSStdD[ iter ]->force_bnd +
                pcFSPassD->pcFSStdD[ iter ]->op_bnd_off;
#else
            force_bnd =
                pcFSPassD->pcFSStdD[ iter ]->force_bnd;
#endif
//@GSM(E-01) end
```

Evaluate()

```
if ( ( redrft_perm ) &&
             ( !pcTargtD->flt_achv ) )
             .....之后的1545-1746
```

F1-F7  pcFSPassD->pcFSStdD[ iter ]->pcUFDD->Log和Xfer_Functions



最后Eval_Delvry_Pass



```
if ( pcLstActFSPassD->pcFSStdD[ iter ]->bnd_enab )
        {
            line_num = __LINE__;
            //-------------------------------------------------------------
            // Apply the flatness vernier to the delivery pass roll bending
            // force.
            //-------------------------------------------------------------
            pcLstActFSPassD->pcFSStdD[ iter ]->force_bnd =
                pcLstActFSPassD->pcFSStdD[ iter ]->force_bnd + pcTargtD->flt_vrn;
        }
        if ( redrft_perm )
        {
            if ( !Copy_Load_Distribution (
                            iter,                       // [-] FSU [hd/bdy/tail] index
                            pcFstFSPassD,               // [-] pointer to first dynamic FSPASS
                                                        //    object
                            pcLstFSPassD,               // [-] pointer to last dynamic FSPASS
                                                        //    object
                            pcFstActFSPassD,            // [-] pointer to first non-dummied
                                                        //    dynamic FSPASS object
                            pcLstActFSPassD             // [-] pointer to last non-dummied
                                                        //    dynamic FSPASS object
                                            ) )
            {
                EMSG << "Copy_Load_Distribution() failed"
                    << END_OF_MESSAGE;
            }
        }
```

