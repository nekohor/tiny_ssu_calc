       //---------------------------------------------------------------
       // Copyright (c) 1999-2003 by
       // Toshiba Mitsubishi-Electric Industrial Systems Corp.
       // TMEIC Corporation
       // Published in only a limited, copyright sense, and all
       // rights, including trade secret rights are reserved.
       //---------------------------------------------------------------
//------------------------------------------------------------------------------
//
//     TITLE:         Profile Envelope Object File
//
//     FILE NAME:     STD$ROOT:[SSU.SOURCE]PENV.CXX
//
//     PREPARED BY:   Toshiba Mitsubishi-Electric Industrial Systems Corp.
//                      Mita 43 MT Bldg. Mita 3-13-16, Minato-ku Tokyo, Japan
//                    TMEIC Corporation
//                      1325 Electric Road, Roanoke, Virginia, USA
//
//     CUSTOMER:      STANDARD
//
//------------------------------------------------------------------------------
//
//     REVISIONS:
//     level   review date  author        change content
//     ------  -----------  ------------  --------------------------------------
//     8.0-0   12-JAN-1999  MH McKinley   Initial hot mill release.
//     8.0-4   23-Jul-1999  TP Hochkeppel Corrected "min" blocks last calc of
//                                        ef_pu_prf_env to use entry pu ef.
//                                        Removed NEWLINE from DMSG'
//     8.0-4   30-SEP-1999  MH McKinley   Removed PCE_THCK_PERT from cPEnv class
//                                            definition.  Data member not used
//                                            anywhere.
//             09-Dec-1999  DT Guidry     Cleaned up includes
//             19-JAN-2000  DT Guidry     Made pcPEnv non-static.
//     8.0-5   05-Oct-2000  Venugopal R   Modified function call from "abs" to
//                                       "fabs" for floating point calculations.
//     8.0-5   12-Nov-2000  Ken McDonald  Removed cSchema::sSchema from zeroData().
//             01-May-2001  TP Hochkeppel Corrected propogation of ef_pu_prf_env
//                                          for dummied passes line 2780
//             31-Oct-2001  G Mor         Corrected limit (both limits were minl) in
//                                        clamp clause in cPnvD::Calculate()-line 1590
//             05-Dec-2001  Venugopal R   Fixed ssu load distribution calcs. Added
//                                        extra argument "iter" in calculate module
//             04-Mar-2002  TP HochKeppel Fixed comment line that appeared like a code
//     10.0-0  06-Jan-2003  AE Broukhiyan Replaced "String" with "MString"
//     15.0-0  10-Mar-2005  Venugopal, R  Visual Studio Net Upgarde
//     16.0-0  12-Mar-2009  Venugopal, R  Added code to support UFD tuning multipliers
//             12-May-2009  SQ Yang       Moved UFD multplier to init().
//------------------------------------------------------------------------------
//
//------------------------------------------------------------------------------
//
//  ABSTRACT:
//
//      FUNCTION/PROCEDURE/TASK  DESCRIPTION
//      -----------------------  -----------------------------------------------
//      Static Class
//          cPEnv                Static PEnv constructor.
//          cPEnv                Static PEnv default constructor.
//          ~cPEnv               Static PEnv destructor.
//          linkObj              Function to link sub-objects.
//          Create_Object        Function to create a static PEnv object.
//          dump                 Function to dump the contents of the static
//                                   PEnv object.
//          zeroData             Function to zero a static PEnv object.
//
//      Dynamic Class
//          cPEnvD               Dynamic PEnv constructor.
//          cPEnvD               Dynamic PEnv default constructor.
//          ~cPEnvD              Dynamic PEnv destructor.
//          linkObj              Function to link sub-objects.
//          Create_Object        Function to create a dynamic PEnv object.
//          dump                 Function to dump the contents of the dynamic
//                                   PEnv object.
//          zeroData             Function to zero a dynamic PEnv object.
//          Create               Function to create the quantities which
//                                   comprise the coordinated envelopes:
//                                       Effective per unit profile
//                                       Rolling force per unit piece width
//                                       UFD roll gap per unit profile
//                                       Per unit profile
//
//------------------------------------------------------------------------------

//-------------------
// MDS include files.
//-------------------
#include "alarm.hxx"
#include "objhash.hxx"
#include "mathuty.hxx"
#include "millparam.hxx"
#include "ufd.hxx"
#include "lpce.hxx"
#include "lrg.hxx"
#include "crlc.hxx"
#include "rollbite.hxx"

//------------------------
// Records include files
//------------------------

//----------------------
// SHARED include files.
//----------------------
#include "pce.hxx"

//-------------------
// SSU include files.
//-------------------
#include "fsstd.hxx"
#include "fspass.hxx"
#include "penv.hxx"

#ifdef WIN32
    #ifdef _DEBUG
    #define new DEBUG_NEW
    #endif
#endif

static const int diagLvl = 0;

//@2ND(M16M062) begin
//-----------------------------------------------------------------------------
// cPEnvD::Calculate_iter0 ABSTRACT:
//     This function creates the quantities which comprise the coordinated
//     envelopes:
//          Effective per unit crown
//          Rolling force per unit piece width
//          UFD roll gap per unit profile
//          Per unit profile
//-----------------------------------------------------------------------------
void cPEnvD::Calculate_iter0(
    const bool            redrft_perm,                  // [-] re-drafting permitted indicator
    const int             iter,                         // [-] iteration indicator
    const cFSPassD* const pcFstFSPassD,                 // [-] pointer to first dynamic FSPASS
                                                        //    object
    const cFSPassD* const pcLstFSPassD,                 // [-] pointer to last dynamic FSPASS
                                                        //    object
    const cFSPassD* const pcFstActFSPassD,              // [-] pointer to first non-dummied
                                                        //    dynamic FSPASS object
    const cFSPassD* const pcLstActFSPassD               // [-] pointer to last non-dummied
                                                        //    dynamic FSPASS object
                   )

{   // Begin of CALCULATE function

    cUFDD::errEnum  ufdd_status;                        // [-] status indicator
    cCRLCD::errEnum crlcd_status;                       // [-] status indicator

    bool  force_bnd_clmp (false);                       // [-] roll bending force clamped
                                                        //    indicator
    bool  force_chg_clmp (false);                       // [-] rolling force per unit width
                                                        //    change clamped indicator
    bool  move_prv[ 2 ];                                // [-] move to previous pass indicator

    int   i                ( 0 );                       // [-] index
    int   loop_count       ( 0 );                       // [-] loop counter
    int   pas_env_lim[ 2 ];                             // [-] pass envelope limit indicator

    float ef_en_pu_prf     ( 0.0F );                    // [mm/mm_in/in] effective entry per
                                                        //    unit profile
    float ef_en_pu_prf_buf ( 0.0F );                    // [mm/mm_in/in] effective entry per
                                                        //    unit profile
    float ef_ex_pu_prf     ( 0.0F );                    // [mm/mm_in/in] effective
                                                        //    exit per unit profile excess
                                                        //    from fixed draft
    float ef_pu_prf_chg    ( 0.0F );                    // [mm/mm_in/in_mm/mm] effective
                                                        //    per unit profile change
    float force_arb        ( 0.0F );                    // [mton/mm_eton/in_kn/mm] arbitrary
                                                        //    delta rolling force per unit
                                                        //    piece width
    float force_bnd_des    ( 0.0F );                    // [mton_eton_kn] desired roll
                                                        //    bending force
    float force_pu_wid_buf ( 0.0F );                    // [mton/mm_eton/in_kn/mm] rolling
                                                        //    force per unit piece width
    float rhdel_sum        ( 0.0F );                    // [mton/mm_eton/in_kn/mm] sum over
                                                        //    relevant passes of (F/W) /
                                                        //    d (per unit roll gap crown)
                                                        //    reflected to delivery pass
    float istd_ex_pu_prf   ( 0.0F );                    // [mm/mm_in/in] interstand
                                                        //    exit per unit profile
    float pce_wr_crn       ( 0.0F );                    // [mm_in] piece to work roll
                                                        //    stack crown
    float scratch          ( 0.0F );                    // [-] scratch
    float std_ex_strn      ( 0.0F );                    // [mm/mm_in/in] stand exit
                                                        //    differential strain
    float ufd_pu_prf       ( 0.0F );                    // [mm/mm_in/in] UFD roll gap
                                                        //    per unit profile
    float wr_br_crn        ( 0.0F );                    // [mm_in_mm] work roll to backup
                                                        //    roll stack crown
    float force_del[ 2 ];                               // [mton/mm_eton/in_kn/mm] rolling
                                                        //    force per unit piece width
                                                        //    width off from the fixed draft
                                                        //    as delivery pass rolling force
                                                        //    per unit piece width
    float force_excess[ 2 ];                            // [-] rolling force per unit piece
                                                        //    width * d (roll gap crown) /
                                                        //    d (F/W) / exit piece thickness
    float force_marg_rem[ 2 ];                          // [mton/mm_eton/mm_kn/mm] rolling
                                                        //    force per unit piece width
                                                        //    margin after fixed per unit
                                                        //    profile adjustment
    float force_pu_arb[ 2 ];                            // [-] per unit change required of
                                                        //    arbitrary force
    float force_resid[ 2 ];                             // [mton/mm_eton/in_kn/mm] residual
                                                        //    rolling force per unit piece
                                                        //    width after fixed per unit
                                                        //    profile adjustment
    float pu_marg[ 2 ];                                 // [-] per unit amount of margin to
                                                        //    retain

    memset( pas_env_lim,    0, 2*sizeof(int) );
    memset( force_del,      0, 2*sizeof(float) );
    memset( force_excess,   0, 2*sizeof(float) );
    memset( force_marg_rem, 0, 2*sizeof(float) );
    memset( force_pu_arb,   0, 2*sizeof(float) );
    memset( force_resid,    0, 2*sizeof(float) );
    memset( pu_marg,        0, 2*sizeof(float) );

    //-------------------------
    // Check for NULL pointers.
    //-------------------------
    MDSVERIFYNAME ( pcFstFSPassD,    "pcFstFSPassD" );
    MDSVERIFYNAME ( pcLstFSPassD,    "pcLstFSPassD" );
    MDSVERIFYNAME ( pcFstActFSPassD, "pcFstActFSPassD" );
    MDSVERIFYNAME ( pcLstActFSPassD, "pcLstActFSPassD" );

    int line_num (0);

    try
    {
        line_num = __LINE__;

//DMSG(-diagLvl) << "Deng gsm test: PEnvD::Calculate !" << END_OF_MESSAGE;

//@2ND(M16M062)_a begin
        if (iter == 0 )
        {
            DMSG(-1) << "Calculate_iter0: PEnvD::Calculate ! iter= "<< iter << END_OF_MESSAGE;
        }
        else
        {
            DMSG(-1) << "Calculate_iter0: PEnvD::Calculate ! iter= "<< iter << END_OF_MESSAGE;
        }
//@2ND(M16M062)_a end

        const cFSPassD* pcFSPassD = pcFstFSPassD;           // [-] pointer to dynamic PASS object

        while ( pcFSPassD != NULL )
        {
            if ( !pcFSPassD->pcFSStdD[ iter ]->dummied )
            {
                line_num = __LINE__;
//DMSG(-diagLvl) << "Deng gsm test: PEnvD::Calculate !" << END_OF_MESSAGE;
                //------------------------------------------------------------------
                // Establish the roll bending force envelope in relation to the
                // minimum / maximum UFD roll gap per unit profile.  In other words,
                // the maximum roll bending force will yield the minimum UFD roll
                // gap per unit profile and the minimum roll bending force will
                // yield the maximum UFD roll gap per unit profile.
                //------------------------------------------------------------------
                pcFSPassD->pcPEnvD->force_bnd_env[ minl ] =
                    pcFSPassD->pcFSStdD[ iter ]->force_bnd_lim[ maxl ];

                pcFSPassD->pcPEnvD->force_bnd_env[ maxl ] =
                    pcFSPassD->pcFSStdD[ iter ]->force_bnd_lim[ minl ];
//@2ND(M16M062)_a begin
                if ( pcFSPassD->pcFSStdD[ iter ]->stdNum >= 5 )
                {
                    pcFSPassD->pcPEnvD->force_bnd_env[ minl ] =
                        pcFSPassD->pcFSStdD[ iter ]->pcFSStd->force_bnd_nom;

                    pcFSPassD->pcPEnvD->force_bnd_env[ maxl ] =
                        pcFSPassD->pcFSStdD[ iter ]->pcFSStd->force_bnd_nom;
                }
//@2ND(M16M062)_a end

                //------------------------------------------------------------------
                // Establish the roll shift position envelope in relation to the
                // minimum / maximum UFD roll gap per unit profile.  In other words,
                // the maximum roll shift position will yield the minimum UFD roll
                // gap per unit profile and the minimum roll shift position yield
                // the maximum UFD roll gap per unit profile.
                //------------------------------------------------------------------
                pcFSPassD->pcPEnvD->pos_shft_env[ minl ] =
                    pcFSPassD->pcFSStdD[ iter ]->wr_shft_lim[ maxl ];

                pcFSPassD->pcPEnvD->pos_shft_env[ maxl ] =
                    pcFSPassD->pcFSStdD[ iter ]->wr_shft_lim[ minl ];

//@2ND(M16M052) begin
                pcFSPassD->pcPEnvD->n_force_bnd_env[ minl ] = pcFSPassD->pcPEnvD->force_bnd_env[ minl ] ;
                pcFSPassD->pcPEnvD->n_force_bnd_env[ maxl ] = pcFSPassD->pcPEnvD->force_bnd_env[ maxl ] ;
                pcFSPassD->pcPEnvD->o_force_bnd_env[ minl ] = pcFSPassD->pcPEnvD->force_bnd_env[ minl ] ;
                pcFSPassD->pcPEnvD->o_force_bnd_env[ maxl ] = pcFSPassD->pcPEnvD->force_bnd_env[ maxl ] ;

                pcFSPassD->pcPEnvD->n_pos_shft_env[ minl ] = pcFSPassD->pcPEnvD->pos_shft_env[ minl ] ;
                pcFSPassD->pcPEnvD->n_pos_shft_env[ maxl ] = pcFSPassD->pcPEnvD->pos_shft_env[ maxl ] ;
                pcFSPassD->pcPEnvD->o_pos_shft_env[ minl ] = pcFSPassD->pcPEnvD->pos_shft_env[ minl ] ;
                pcFSPassD->pcPEnvD->o_pos_shft_env[ maxl ] = pcFSPassD->pcPEnvD->pos_shft_env[ maxl ] ;
//@2ND(M16M052) end

                DMSG( -diagLvl ) << "@@Min@@,pos_shft_env =  "<< pcFSPassD->pcPEnvD->pos_shft_env[ minl ] << ",std No=" <<pcFSPassD->pcFSStdD[ iter ]->stdNum << END_OF_MESSAGE;
                DMSG( -diagLvl ) << "@@Max@@,pos_shft_env =  "<< pcFSPassD->pcPEnvD->pos_shft_env[ maxl ] << ",std No=" <<pcFSPassD->pcFSStdD[ iter ]->stdNum << END_OF_MESSAGE;
                //------------------------------------------------------------------
                // Establish the pair cross angle envelope in relation to the
                // minimum / maximum UFD roll gap per unit profile.  In other words,
                // the maximum pair cross angle will yield the minimum UFD roll gap
                // per unit profile and the minimum pair cross angle yield the
                // maximum UFD roll gap per unit profile.
                //------------------------------------------------------------------
                pcFSPassD->pcPEnvD->angl_pc_env[ minl ] =
                    pcFSPassD->pcFSStdD[ iter ]->angl_pc_lim[ maxl ];

                pcFSPassD->pcPEnvD->angl_pc_env[ maxl ] =
                    pcFSPassD->pcFSStdD[ iter ]->angl_pc_lim[ minl ];
//DMSG(-diagLvl) << "Deng gsm test: PEnvD::Calculate !" << END_OF_MESSAGE;

                for ( i = minl; i <= maxl; i++ )
                {
                    line_num = __LINE__;
                    //---------------------------------------------------------
                    // Establish the minimum / maximum piece to work roll stack
                    // crown and work roll to backup roll stack crown limits.
                    //---------------------------------------------------------
                    pcFSPassD->pcFSStdD[ iter ]->pcCRLCD->Crns(
                              pcFSPassD->pcFSStdD[ iter ]->wr_shft_lim [ i ],
                              pcFSPassD->pcFSStdD[ iter ]->angl_pc_lim [ i ],
                              pcFSPassD->pcPEnvD->pce_wr_crn_lim       [ i ],
                              pcFSPassD->pcPEnvD->wr_br_crn_lim        [ i ] );
                }
                //--------------------------------------------------
                // Calculate the rolling force per unit piece width.
                //--------------------------------------------------
                line_num = __LINE__;
                pcFSPassD->pcPEnvD->force_pu_wid =
                    pcFSPassD->pcFSStdD[ iter ]->force_strip /
                    pcFSPassD->pcFSStdD[ iter ]->pcEnPceD->width;

                if ( redrft_perm )
                {
                    //---------------------------------------------------------
                    // Calculate the minimum and maximum rolling force per unit
                    // piece width limits.
                    //---------------------------------------------------------
                    line_num = __LINE__;
                    pcFSPassD->pcPEnvD->force_pu_wid_lim[ minl ] =
                        pcFSPassD->pcPEnvD->force_pu_wid *
                        ( 1.0F - pcFSPassD->pcFSPass->force_pert );

                    pcFSPassD->pcPEnvD->force_pu_wid_lim[ maxl ] =
                        pcFSPassD->pcPEnvD->force_pu_wid *
                        ( 1.0F + pcFSPassD->pcFSPass->force_pert );

                    for ( i = minl; i <= maxl; i++ )
                    {
                        line_num = __LINE__;
                        if ( pcFSPassD->pcPEnvD->force_pu_wid_lim[ i ] <
                                 pcFSPassD->pcPEnvD->pcPEnv->force_lim_mn /
                                 pcFSPassD->pcFSStdD[ iter ]->pcExPceD->width )
                        {
                            //----------------------------------------------------
                            // Set the rolling force per unit piece width limit to
                            // greater than the absolute minimum rolling force per
                            // unit piece width limit.
                            //----------------------------------------------------
                            line_num = __LINE__;
                            pcFSPassD->pcPEnvD->force_pu_wid_lim[ i ] =
                                pcFSPassD->pcPEnvD->pcPEnv->force_lim_mn /
                                ( pcFSPassD->pcPEnvD->pcPEnv->force_adj_mod *
                                pcFSPassD->pcFSStdD[ iter ]->pcExPceD->width );
                        }
                    }
                }
                else
                {
                    for ( i = minl; i <= maxl; i++ )
                    {
                        pcFSPassD->pcPEnvD->force_pu_wid_lim[ i ] =
                            pcFSPassD->pcPEnvD->force_pu_wid;
                    }
                }
//DMSG(-diagLvl) << "Deng gsm test: PEnvD::Calculate !" << END_OF_MESSAGE;
               //----------------------------------------------------------------
                // Establish the minimum / maximum piece to work roll stack crown
                // and work roll to backup roll stack crown for nominal pair cross
                // angle and nominal roll shift position.
                //----------------------------------------------------------------
                line_num = __LINE__;
                pcFSPassD->pcFSStdD[ iter ]->pcCRLCD->Crns(
//@2ND(M16M052) begin
                          //pcFSPassD->pcFSStdD[ iter ]->pcFSStd->wr_shft_nom,
                          (pcFSPassD->pcFSStdD[ iter ]->wr_shft_lim[ maxl ] + pcFSPassD->pcFSStdD[ iter ]->wr_shft_lim[ minl ] )/2,
//@2ND(M16M052) end
                          pcFSPassD->pcFSStdD[ iter ]->pcFSStd->angl_pc_nom,
                          pce_wr_crn,
                          wr_br_crn );

                //----------------------------------------------------------------
                // Calculate the UFD roll roll gap profile derivative with respect
                // rolling force per unit piece width.
                //----------------------------------------------------------------
                pcFSPassD->pcPEnvD->dprf_dfrcw =
                    pcFSPassD->pcFSStdD[ iter ]->pcUFDD->Dprf_Dfrcw (
                                pcFSPassD->pcPEnvD->force_pu_wid,
                                pcFSPassD->pcFSStdD[ iter ]->pcFSStd->force_bnd_nom,
                                pce_wr_crn,
                                wr_br_crn                           );
//DMSG(-diagLvl) << "Deng gsm test: PEnvD::Calculate !" << END_OF_MESSAGE;

                //-----------------------------------------------------------------
                // Initialize the rolling force per unit width piece envelope.
                // Note: The UFD roll gap profile derivative is used for direction.
                //-----------------------------------------------------------------
                if ( 0.0 <= pcFSPassD->pcPEnvD->dprf_dfrcw )
                {
                    pcFSPassD->pcPEnvD->force_pu_wid_env[ minl ] =
                        pcFSPassD->pcPEnvD->force_pu_wid_lim[ minl ];
                    pcFSPassD->pcPEnvD->force_pu_wid_env[ maxl ] =
                        pcFSPassD->pcPEnvD->force_pu_wid_lim[ maxl ];
                }
                else
                {
                    pcFSPassD->pcPEnvD->force_pu_wid_env[ minl ] =
                        pcFSPassD->pcPEnvD->force_pu_wid_lim[ maxl ];
                    pcFSPassD->pcPEnvD->force_pu_wid_env[ maxl ] =
                        pcFSPassD->pcPEnvD->force_pu_wid_lim[ minl ];
                }
//DMSG(-diagLvl) << "Deng gsm test: PEnvD::Calculate !" << END_OF_MESSAGE;
                //------------------------------------------------------------
                // Initialize the piece to work roll stack crown and work roll
                // backup roll stack crown envelopes.
                //------------------------------------------------------------
                pcFSPassD->pcPEnvD->pce_wr_crn_env[ minl ] =
                    pcFSPassD->pcPEnvD->pce_wr_crn_lim[ maxl ];
                pcFSPassD->pcPEnvD->wr_br_crn_env[ minl ] =
                    pcFSPassD->pcPEnvD->wr_br_crn_lim[ maxl ];
                pcFSPassD->pcPEnvD->pce_wr_crn_env[ maxl ] =
                    pcFSPassD->pcPEnvD->pce_wr_crn_lim[ minl ];
                pcFSPassD->pcPEnvD->wr_br_crn_env[ maxl ] =
                    pcFSPassD->pcPEnvD->wr_br_crn_lim[ minl ];

                for ( i = minl; i <= maxl; i++ )
                {
                    //--------------------------------------------------------------
                    // Establish the minimum / maximum UFD roll gap per unit profile
                    // envelope.
                    //--------------------------------------------------------------
                    line_num = __LINE__;
                    pcFSPassD->pcPEnvD->ufd_pu_prf_env[ i ] =
                        pcFSPassD->pcFSStdD[ iter ]->pcUFDD->Prf(
                             pcFSPassD->pcPEnvD->force_pu_wid_env [ i ],
                             pcFSPassD->pcPEnvD->force_bnd_env    [ i ],
                             pcFSPassD->pcPEnvD->pce_wr_crn_env   [ i ],
                             pcFSPassD->pcPEnvD->wr_br_crn_env    [ i ] ) /
                        pcFSPassD->pcFSStdD[ iter ]->pcExPceD->thick;
                }

                DMSG( -diagLvl ) << "@@minl@@,thick            =  "<< pcFSPassD->pcFSStdD[ iter ]->pcExPceD->thick << ",std No=" <<pcFSPassD->pcFSStdD[ iter ]->stdNum << END_OF_MESSAGE;

                DMSG( -diagLvl ) << "@@minl@@,ef_pu_prf_env    =  "<< pcFSPassD->pcPEnvD->ufd_pu_prf_env[ minl ] << ",std No=" <<pcFSPassD->pcFSStdD[ iter ]->stdNum << END_OF_MESSAGE;
                DMSG( -diagLvl ) << "@@minl@@,force_pu_wid_env =  "<< pcFSPassD->pcPEnvD->force_pu_wid_env[ minl ] << ",std No=" <<pcFSPassD->pcFSStdD[ iter ]->stdNum << END_OF_MESSAGE;
                DMSG( -diagLvl ) << "@@minl@@,force_bnd_env    =  "<< pcFSPassD->pcPEnvD->force_bnd_env[ minl ] << ",std No=" <<pcFSPassD->pcFSStdD[ iter ]->stdNum << END_OF_MESSAGE;
                DMSG( -diagLvl ) << "@@minl@@,pce_wr_crn_env   =  "<< pcFSPassD->pcPEnvD->pce_wr_crn_env[ minl ] << ",std No=" <<pcFSPassD->pcFSStdD[ iter ]->stdNum << END_OF_MESSAGE;
                DMSG( -diagLvl ) << "@@minl@@,wr_br_crn_env    =  "<< pcFSPassD->pcPEnvD->wr_br_crn_env[ minl ] << ",std No=" <<pcFSPassD->pcFSStdD[ iter ]->stdNum << END_OF_MESSAGE;

                DMSG( -diagLvl ) << "@@maxl@@,ef_pu_prf_env    =  "<< pcFSPassD->pcPEnvD->ufd_pu_prf_env[ maxl ] << ",std No=" <<pcFSPassD->pcFSStdD[ iter ]->stdNum << END_OF_MESSAGE;
                DMSG( -diagLvl ) << "@@maxl@@,force_pu_wid_env =  "<< pcFSPassD->pcPEnvD->force_pu_wid_env[ maxl ] << ",std No=" <<pcFSPassD->pcFSStdD[ iter ]->stdNum << END_OF_MESSAGE;
                DMSG( -diagLvl ) << "@@maxl@@,force_bnd_env    =  "<< pcFSPassD->pcPEnvD->force_bnd_env[ maxl ] << ",std No=" <<pcFSPassD->pcFSStdD[ iter ]->stdNum << END_OF_MESSAGE;
                DMSG( -diagLvl ) << "@@maxl@@,pce_wr_crn_env   =  "<< pcFSPassD->pcPEnvD->pce_wr_crn_env[ maxl ] << ",std No=" <<pcFSPassD->pcFSStdD[ iter ]->stdNum << END_OF_MESSAGE;
                DMSG( -diagLvl ) << "@@maxl@@,wr_br_crn_env    =  "<< pcFSPassD->pcPEnvD->wr_br_crn_env[ maxl ] << ",std No=" <<pcFSPassD->pcFSStdD[ iter ]->stdNum << END_OF_MESSAGE;

            }
            for ( i = we; i <= cb; i++ )
            {
                //----------------------------------------------------------------
                // Retrieve the piece critical buckling limits for the given pass.
                //----------------------------------------------------------------
                line_num = __LINE__;
                pcFSPassD->pcPEnvD->std_ex_strn_lim[ i ] =
                    pcFSPassD->pcLPceD->Crit_Bckl_Lim( i );
            }
//DMSG(-diagLvl) << "Deng gsm test: PEnvD::Calculate !" << END_OF_MESSAGE;
            // if influence is considered zero(close to), reverse the upstream
            // PE profile limits.  This will allow "reversed" force changes on
            // passes that do not influence the final profile
            if ( pcFSPassD->pcFSStdD[ iter ]->pcLRGD->pce_infl_cof <
                     pcFSPassD->pcPEnvD->pcPEnv->pce_infl_cof_mn )
            {
                if ( pcFSPassD->pcPass->num > pcFstActFSPassD->pcPass->num )
                {
                    if ( redrft_perm &&
                         pcFSPassD->pcPrvAct->pcPEnvD->force_pu_wid_lim[ minl ] !=
                             pcFSPassD->pcPrvAct->pcPEnvD->force_pu_wid_lim[ maxl ] )
                    {
                        pcFSPassD->pcPrvAct->pcPEnvD->ef_pu_prf_lim[ minl ] = 1.0;
                        pcFSPassD->pcPrvAct->pcPEnvD->ef_pu_prf_lim[ maxl ] = - 1.0;
                    }
                    else
                    {
                        pcFSPassD->pcPrvAct->pcPEnvD->ef_pu_prf_lim[ minl ] = - 1.0;
                        pcFSPassD->pcPrvAct->pcPEnvD->ef_pu_prf_lim[ maxl ] = 1.0;
                    }
                }
                else
                {
                    pcFSPassD->pcPrvAct->pcPEnvD->ef_pu_prf_lim[ minl ] = - 1.0;
                    pcFSPassD->pcPrvAct->pcPEnvD->ef_pu_prf_lim[ maxl ] = 1.0;
                }
            }
            else
            {
                //-------------------------------------------------
                // Calculate the effective per unit profile limits.
                //-------------------------------------------------

                //line_num = __LINE__;
                //pcFSPassD->pcPrvAct->pcPEnvD->ef_pu_prf_lim[ minl ] =
                //    pcFSPassD->pcFSStdD[ iter ]->pcLRGD->Ef_En_PU_Prf1(
                //               pcFSPassD->pcPEnvD->ufd_pu_prf_env  [ minl ],
                //               pcFSPassD->pcPEnvD->std_ex_strn_lim [ we ] );

                //line_num = __LINE__;
                //pcFSPassD->pcPrvAct->pcPEnvD->ef_pu_prf_lim[ maxl ] =
                //    pcFSPassD->pcFSStdD[ iter ]->pcLRGD->Ef_En_PU_Prf1(
                //               pcFSPassD->pcPEnvD->ufd_pu_prf_env  [ maxl ],
                //               pcFSPassD->pcPEnvD->std_ex_strn_lim [ cb ] );

                line_num = __LINE__;
                pcFSPassD->pcPrvAct->pcPEnvD->ef_pu_prf_lim[ minl ] =
                    pcFSPassD->pcFSStdD[ iter ]->pcLRGD->Ef_En_PU_Prf1(
                               pcFSPassD->pcPEnvD->ufd_pu_prf_env  [ minl ],
                               pcFSPassD->pcPEnvD->std_ex_strn_lim [ we ] );

                line_num = __LINE__;
                pcFSPassD->pcPrvAct->pcPEnvD->ef_pu_prf_lim[ maxl ] =
                    pcFSPassD->pcFSStdD[ iter ]->pcLRGD->Ef_En_PU_Prf1(
                               pcFSPassD->pcPEnvD->ufd_pu_prf_env  [ maxl ],
                               pcFSPassD->pcPEnvD->std_ex_strn_lim [ cb ] );


                pcFSPassD->pcPrvAct->pcPEnvD->ef_pu_prf_lim[ minl ] = - 2.01F;
                pcFSPassD->pcPrvAct->pcPEnvD->ef_pu_prf_lim[ maxl ] =   2.01F;


            }
            if ( pcFSPassD == pcLstFSPassD )
            {
                break;
            }
            else
            {
                //----------------------------------------------
                // Increment pointer to the dynamic PASS object.
                //----------------------------------------------
                pcFSPassD = ( cFSPassD* )( pcFSPassD->next_obj );
            }
        }
        //-------------------------------------------------------------------------
        // Since the mill target per unit can change, do not constrain the delivery
        // pass,
        //-------------------------------------------------------------------------
//DMSG(-diagLvl) << "Deng gsm test: PEnvD::Calculate !" << END_OF_MESSAGE;
        pcLstActFSPassD->pcPEnvD->ef_pu_prf_lim[ minl ] = -1.0;
        pcLstActFSPassD->pcPEnvD->ef_pu_prf_lim[ maxl ] = 1.0;

        for ( i = minl; i <= maxl; i++ )
        {
            //--------------------------------------------------------
            // Initialize first pass effective entry per unit profile.
            //--------------------------------------------------------
            ( ( cFSPassD* )(pcFstFSPassD->previous_obj) )->pcPEnvD->ef_pu_prf_env[ i ] =
                ( ( cFSPassD* )(pcFstFSPassD->previous_obj) )->pcLPceD->ef_pu_prf;

            //---------------------------------------
            // Initialize the limiting pass envelope.
            //---------------------------------------
            pas_env_lim[ i ] =
                ( ( cFSPassD* )(pcFstFSPassD->previous_obj) )->pcPass->num;
        }

        //---------------------------------------------------------
        //*********************************************************
        // CREATE THE COORDINATED ENVELOPES WHICH ARE COMPRISED OF:
        //     Effective exit per unit profile
        //     UFD roll gap per unit profile
        //     Rolling force per unit piece width
        //---------------------------------------------------------
//DMSG(-diagLvl) << "Deng gsm test: PEnvD::Calculate !" << END_OF_MESSAGE;

        pcFSPassD = pcFstActFSPassD;
        while ( pcFSPassD != NULL )
        {
//DMSG(-diagLvl) << "Deng gsm test: PEnvD::Calculate !" << END_OF_MESSAGE;
            //-------------------------------------------------------
            //*******************************************************
            // DETERMINE THE MINIMUM ENVELOPE COMPONENTS:
            //     Effective exit per unit profile.
            //     UFD roll gap per unit profile
            //     Rolling force per unit piece width
            //-------------------------------------------------------
            move_prv[ minl ] = false;

            //------------------------------------------------------------------
            // Calculate the effective per unit profile component of the
            // minimum envelope for the given conditions.
            //------------------------------------------------------------------
            DMSG( -diagLvl ) << "@@Min@@,ef_pu_prf_env      =  "<< pcFSPassD->pcPEnvD->ef_pu_prf_env[ minl ] << ",std No=" <<pcFSPassD->pcFSStdD[ iter ]->stdNum << END_OF_MESSAGE;

            line_num = __LINE__;
            pcFSPassD->pcPEnvD->ef_pu_prf_env[ minl ] =
                pcFSPassD->pcFSStdD[ iter ]->pcLRGD->Ef_Ex_PU_Prf3 (
                               pcFSPassD->pcLPceD->strn_rlf_cof,
                               pcFSPassD->pcPrvAct->pcPEnvD->ef_pu_prf_env[ minl ],
                               pcFSPassD->pcPEnvD->ufd_pu_prf_env[ minl ] );

            //ef_en_pu_prf + ( 1.0 - pce_infl_cof + ( 1.0 - pcLRG->prf_recv_cof ) *
            //strn_rlf_cof * pce_infl_cof ) * ( ufd_pu_prf - ef_en_pu_prf ) /
            //prf_chg_attn_fac;

            DMSG( -diagLvl ) << "@@Min@@,strn_rlf_cof       =  "<< pcFSPassD->pcLPceD->strn_rlf_cof << ",std No=" <<pcFSPassD->pcFSStdD[ iter ]->stdNum << END_OF_MESSAGE;
            DMSG( -diagLvl ) << "@@Min@@,pce_infl_cof       =  "<<pcFSPassD->pcFSStdD[ iter ]->pcLRGD->pce_infl_cof << ",std No=" <<pcFSPassD->pcFSStdD[ iter ]->stdNum << END_OF_MESSAGE;
            //DMSG( -diagLvl ) << "@@Min@@,prf_recv_cof       =  "<<pcFSPassD->pcFSStdD[ iter ]->pcLRGD->pcLRG->prf_recv_cof << ",std No=" <<pcFSPassD->pcFSStdD[ iter ]->stdNum << END_OF_MESSAGE;
            DMSG( -diagLvl ) << "@@Min@@,prf_chg_attn_fac   =  "<<pcFSPassD->pcFSStdD[ iter ]->pcLRGD->prf_chg_attn_fac << ",std No=" <<pcFSPassD->pcFSStdD[ iter ]->stdNum << END_OF_MESSAGE;

            DMSG( -diagLvl ) << "@@Min@@,ef_pu_prf_env_p    =  "<< pcFSPassD->pcPrvAct->pcPEnvD->ef_pu_prf_env[ minl ] << ",std No=" <<pcFSPassD->pcFSStdD[ iter ]->stdNum << END_OF_MESSAGE;
            DMSG( -diagLvl ) << "@@Min@@,ef_pu_prf_env      =  "<< pcFSPassD->pcPEnvD->ef_pu_prf_env[ minl ] << ",std No=" <<pcFSPassD->pcFSStdD[ iter ]->stdNum << END_OF_MESSAGE;
            DMSG( -diagLvl ) << "@@Min@@,ufd_pu_prf_env     =  "<< pcFSPassD->pcPEnvD->ufd_pu_prf_env[ minl ] << ",std No=" <<pcFSPassD->pcFSStdD[ iter ]->stdNum << END_OF_MESSAGE;
            DMSG( -diagLvl ) << "@@Min@@,ef_pu_prf_lim      =  "<< pcFSPassD->pcPEnvD->ef_pu_prf_lim [ minl ] << ",std No=" <<pcFSPassD->pcFSStdD[ iter ]->stdNum << END_OF_MESSAGE;


            // If we are lower than lowest puefprf required of this pass
            if ( pcFSPassD->pcPEnvD->ef_pu_prf_env[ minl ] <
                     pcFSPassD->pcPEnvD->ef_pu_prf_lim[ minl ] )
            {
                // try to save force changes for other passes
                // if down stream pass is at its crown and bending limits
                if ( pcFSPassD != pcLstActFSPassD &&
                     pcFSPassD->pcNxtAct->pcPEnvD->pce_wr_crn_env[ minl ] ==
                         pcFSPassD->pcNxtAct->pcPEnvD->pce_wr_crn_lim[ maxl ] &&
                     pcFSPassD->pcNxtAct->pcPEnvD->wr_br_crn_env[ minl ] ==
                         pcFSPassD->pcNxtAct->pcPEnvD->wr_br_crn_lim[ maxl ] &&
                     pcFSPassD->pcNxtAct->pcPEnvD->force_bnd_env[ minl ] ==
                         pcFSPassD->pcNxtAct->pcFSStdD[ iter ]->force_bnd_lim[ maxl ] )
                {
                    //-------------------------------------------------------------
                    // The highest pass encountered is defined as the limiting pass
                    // with respect to the effective per unit crown envelope.
                    //-------------------------------------------------------------
                    pas_env_lim[ minl ] =
                        cMathUty::Max( pcFSPassD->pcNxtAct->pcPass->num,
                                       pas_env_lim[ minl ] );
                }
                // aim this pass to the downstream limit
                ef_ex_pu_prf = pcFSPassD->pcPEnvD->ef_pu_prf_lim[ minl ];

                //----------------------------------------------------------
                // Calculate the UFD roll gap per unit profile for the given
                // conditions.
                //----------------------------------------------------------
                line_num = __LINE__;
                ufd_pu_prf =
                    pcFSPassD->pcFSStdD[ iter ]->pcLRGD->UFD_PU_Prf3 (
                               pcFSPassD->pcLPceD->strn_rlf_cof,
                               pcFSPassD->pcPrvAct->pcPEnvD->ef_pu_prf_env[ minl ],
                               ef_ex_pu_prf                          );

                // if desired ufd == ef exit it was not possible to change ufd
                ufdd_status = cUFDD::undef;
                if ( ufd_pu_prf != ef_ex_pu_prf )
                {
                    //----------------------------------------------------
                    // Select a higher rolling force per unit piece width.
                    //----------------------------------------------------
                    line_num = __LINE__;
                    pcFSPassD->pcFSStdD[ iter ]->pcUFDD->Frc_PU_Wid(
                               ufd_pu_prf * pcFSPassD->pcFSStdD[ iter ]->pcExPceD->thick,
                               pcFSPassD->pcPEnvD->force_bnd_env[ minl ],
                               pcFSPassD->pcPEnvD->pce_wr_crn_env[ minl ],
                               pcFSPassD->pcPEnvD->wr_br_crn_env[ minl ],
                               force_pu_wid_buf,
                               ufdd_status );

                    if ( ufdd_status != cUFDD::valid )
                    {
                        DMSG( diagLvl )
                            << "Calculate: PID="
                            << pcFSPassD->pcExPceD[ iter ]->pcPce->prod_id
                            << ", UFDD Frc_PU_Wid status="
                            << cUFDD::Image( ufdd_status )
                            << END_OF_MESSAGE;
                    }
                }
                if ( ufdd_status != cUFDD::valid )
                {   // set desired force to an extreme value NORMALLY positive
                    force_pu_wid_buf =
                        pcFSPassD->pcPEnvD->force_pu_wid_lim[ maxl ] + 10.0F;
                    if ( pcFSPassD->pcPEnvD->dprf_dfrcw < 0.0F )
                    {
                        force_pu_wid_buf =
                            pcFSPassD->pcPEnvD->force_pu_wid_lim[ minl ] - 10.0F;
                    }
                }

                //------------------------------------------------------------------
                // Restrict the minimum rolling force per unit piece width component
                // of the envelope to within the rolling force per unit piece width
                // limits.
                //------------------------------------------------------------------
                line_num = __LINE__;
                pcFSPassD->pcPEnvD->force_pu_wid_env[ minl ] =
                    cMathUty::Clamp( force_pu_wid_buf,
                                     pcFSPassD->pcPEnvD->force_pu_wid_lim[ minl ],
                                     pcFSPassD->pcPEnvD->force_pu_wid_lim[ maxl ] );

                //--------------------------------------------------------------
                // Indicate that the required rolling force per unit piece width
                // change was restricted.
                //--------------------------------------------------------------
                force_chg_clmp =
                    pcFSPassD->pcPEnvD->force_pu_wid_env[ minl ] != force_pu_wid_buf;

                if ( force_chg_clmp &&
                     pcFSPassD->pcFSStdD[ iter ]->pcLRGD->pce_infl_cof >
                         pcFSPassD->pcPEnvD->pcPEnv->pce_infl_cof_mn )
                {
                    force_chg_clmp = false;

                    //--------------------------------------------------------------
                    // Attempt to change the effective entry per unit profile.  This
                    // will not help the current pass rolling force per unit piece
                    // width, but may change the previous pass rolling force per
                    // unit piece width.  Use the piece critical buckling limit for
                    // a wavy edge flatness defect as a possible starting point.
                    //--------------------------------------------------------------
                    line_num = __LINE__;
                    istd_ex_pu_prf =
                        pcFSPassD->pcFSStdD[ iter ]->pcLRGD->Istd_Ex_PU_Prf0 (
                                   pcFSPassD->pcLPceD->strn_rlf_cof,
                                   pcFSPassD->pcPEnvD->std_ex_strn_lim[ we ],
                                   ef_ex_pu_prf                              );

                    line_num = __LINE__;
                    ef_en_pu_prf =
                        pcFSPassD->pcFSStdD[ iter ]->pcLRGD->Ef_En_PU_Prf5 (
                                   pcFSPassD->pcLPceD->strn_rlf_cof,
                                   pcFSPassD->pcPEnvD->std_ex_strn_lim[ we ],
                                   istd_ex_pu_prf                          );

                    //------------------------------------------------------------
                    // Restrict the effective entry per unit profile to within the
                    // effective per unit profile envelope.
                    //------------------------------------------------------------
                    line_num = __LINE__;
                    ef_en_pu_prf_buf =
                        cMathUty::Clamp( ef_en_pu_prf,
                                         pcFSPassD->pcPrvAct->pcPEnvD->ef_pu_prf_env[ minl ],
                                         pcFSPassD->pcPrvAct->pcPEnvD->ef_pu_prf_env[ maxl ] );

                    //---------------------------------------------------------
                    // Indicate that a move should be made to the previous non-
                    // dummied pass if an effective per unit profile change is
                    // possible.
                    //---------------------------------------------------------
                    line_num = __LINE__;
                    move_prv[ minl ] =
                        ( ef_en_pu_prf_buf !=
                            pcFSPassD->pcPrvAct->pcPEnvD->ef_pu_prf_env[ minl ] ) &&
                        ( pcFSPassD->pcPrvAct->pcPEnvD->ef_pu_prf_env[ minl ] !=
                            pcFSPassD->pcPrvAct->pcPEnvD->ef_pu_prf_env[ maxl ] );

                    //------------------------------------------------------------
                    // Capture the minimum effective entry per unit profile limit.
                    //------------------------------------------------------------
                    pcFSPassD->pcPrvAct->pcPEnvD->ef_pu_prf_lim[ minl ] = ef_en_pu_prf_buf;

                    if ( !move_prv[ minl ] )
                    {
                        ef_en_pu_prf_buf =
                            pcFSPassD->pcPrvAct->pcPEnvD->ef_pu_prf_env[ minl ];
                    }
                }
                //----------------------------------------------------------
                // Calculate the UFD roll gap per unit profile for the given
                // conditions.
                //----------------------------------------------------------
                line_num = __LINE__;
                ufd_pu_prf =
                    pcFSPassD->pcFSStdD[ iter ]->pcLRGD->UFD_PU_Prf3 (
                         pcFSPassD->pcLPceD->strn_rlf_cof,
                         ef_en_pu_prf_buf,
                         ef_ex_pu_prf                                );
//@2ND(M16M083) begin
    //            float pce_wr_crn_temp =
    //                pcUFDD->Pce_WR_Crn( pcAlcD->ufd_pu_prf *
    //                                    pcAlcD->thick,
    //                                    pcAlcD->force_pu_wid,
    //                                    pcStdD->force_bnd,
    //                                    wr_br_crn );

    //            //Deng test, change 
                //pce_wr_crn = pce_wr_crn_temp;
//@2ND(M16M083) ebd

                //----------------------------------------------------
                // Calculate the work roll crown change and adjust the
                // minimum piece to work roll and minimum work roll to
                // backup roll stack crown envelope components.
                //----------------------------------------------------
                line_num = __LINE__;
                pcFSPassD->pcFSStdD[ iter ]->pcUFDD->Crns(
                          ufd_pu_prf * pcFSPassD->pcFSStdD[ iter ]->pcExPceD->thick,
                          pcFSPassD->pcPEnvD->force_pu_wid_env[ minl ],
                          pcFSPassD->pcPEnvD->force_bnd_env[ minl ],
                          pce_wr_crn,
                          wr_br_crn );

                //-----------------------------------------------------------
                // Calculate the minimum roll shift position component of the
                // envelope for the given conditions.
                //-----------------------------------------------------------
                line_num = __LINE__;
                DMSG( -diagLvl ) << "@@Min@@,pos_shft_env =  "<< pcFSPassD->pcPEnvD->pos_shft_env[ minl ] << ",std No=" <<pcFSPassD->pcFSStdD[ iter ]->stdNum << END_OF_MESSAGE;
                DMSG( -diagLvl ) << "@@Max@@,pos_shft_env =  "<< pcFSPassD->pcPEnvD->pos_shft_env[ maxl ] << ",std No=" <<pcFSPassD->pcFSStdD[ iter ]->stdNum << END_OF_MESSAGE;

                pcFSPassD->pcFSStdD[ iter ]->pcCRLCD->Shft_Pos(
                              pce_wr_crn,
                              pcFSPassD->pcPEnvD->angl_pc_env  [ minl ],
                              pcFSPassD->pcFSStdD[ iter ]->wr_shft_lim,
                              pcFSPassD->pcPEnvD->pos_shft_env [ minl ],
                              crlcd_status );

                DMSG( -diagLvl ) << "@@Min@@,pos_shft_env =  "<< pcFSPassD->pcPEnvD->pos_shft_env[ minl ] << ",std No=" <<pcFSPassD->pcFSStdD[ iter ]->stdNum << END_OF_MESSAGE;
                DMSG( -diagLvl ) << "@@Max@@,pos_shft_env =  "<< pcFSPassD->pcPEnvD->pos_shft_env[ maxl ] << ",std No=" <<pcFSPassD->pcFSStdD[ iter ]->stdNum << END_OF_MESSAGE;

                if ( crlcd_status != cCRLCD::valid )
                {
                    DMSG( diagLvl )
                        << "Calculate:PID="
                        << pcFSPassD->pcExPceD[ iter ]->pcPce->prod_id
                        << ", CRLCD Crns status="
                        << cCRLCD::Image( crlcd_status )
                        << END_OF_MESSAGE;
                }
                //------------------------------------------------------------------
                // Re-calculate the following composite roll stack crown quantities:
                //     Piece to work roll stack crown
                //     Work roll to backup roll stack crown
                //------------------------------------------------------------------
                line_num = __LINE__;
                pcFSPassD->pcFSStdD[ iter ]->pcCRLCD->Crns(
                          pcFSPassD->pcPEnvD->pos_shft_env  [ minl ],
                          pcFSPassD->pcPEnvD->angl_pc_env   [ minl ],
                          pcFSPassD->pcPEnvD->pce_wr_crn_env[ minl ],
                          pcFSPassD->pcPEnvD->wr_br_crn_env [ minl ] );

                DMSG( -diagLvl ) << "@@Min@@,pos_shft_env =  "<< pcFSPassD->pcPEnvD->pos_shft_env[ minl ] << ",std No=" <<pcFSPassD->pcFSStdD[ iter ]->stdNum << END_OF_MESSAGE;
                DMSG( -diagLvl ) << "@@Max@@,pos_shft_env =  "<< pcFSPassD->pcPEnvD->pos_shft_env[ maxl ] << ",std No=" <<pcFSPassD->pcFSStdD[ iter ]->stdNum << END_OF_MESSAGE;

                //--------------------------------------------------------------
                // Calculate the minimum piece to work roll stack crown envelope
                // component.
                //--------------------------------------------------------------
                line_num = __LINE__;
                pce_wr_crn =
                    pcFSPassD->pcFSStdD[ iter ]->pcUFDD->Pce_WR_Crn (
                            ufd_pu_prf * pcFSPassD->pcFSStdD[ iter ]->pcExPceD->thick,
                            pcFSPassD->pcPEnvD->force_pu_wid_env[ minl ],
                            pcFSPassD->pcPEnvD->force_bnd_env[ minl ],
                            pcFSPassD->pcPEnvD->wr_br_crn_env[ minl ] );

                //-----------------------------------------------------------------
                // Calculate the minimum pair cross angle component of the envelope
                // for the given conditions.
                //-----------------------------------------------------------------
                line_num = __LINE__;
                pcFSPassD->pcFSStdD[ iter ]->pcCRLCD->PC_Angl(
                             pce_wr_crn,
                             pcFSPassD->pcPEnvD->angl_pc_env[ minl ],
                             pcFSPassD->pcFSStdD[ iter ]->angl_pc_lim );

                //------------------------------------------------------------------
                // Re-calculate the following composite roll stack crown quantities:
                //     Piece to work roll stack crown
                //     Work roll to backup roll stack crown
                //------------------------------------------------------------------
                line_num = __LINE__;
                pcFSPassD->pcFSStdD[ iter ]->pcCRLCD->Crns(
                          pcFSPassD->pcPEnvD->pos_shft_env  [ minl ],
                          pcFSPassD->pcPEnvD->angl_pc_env   [ minl ],
                          pcFSPassD->pcPEnvD->pce_wr_crn_env[ minl ],
                          pcFSPassD->pcPEnvD->wr_br_crn_env [ minl ] );

                DMSG( -diagLvl ) << "@@Min@@,pos_shft_env =  "<< pcFSPassD->pcPEnvD->pos_shft_env[ minl ] << ",std No=" <<pcFSPassD->pcFSStdD[ iter ]->stdNum << END_OF_MESSAGE;
                DMSG( -diagLvl ) << "@@Max@@,pos_shft_env =  "<< pcFSPassD->pcPEnvD->pos_shft_env[ maxl ] << ",std No=" <<pcFSPassD->pcFSStdD[ iter ]->stdNum << END_OF_MESSAGE;
                DMSG( -diagLvl ) << "@@Min@@,force_bnd_env =  "<< pcFSPassD->pcPEnvD->force_bnd_env[ minl ] << ",std No=" <<pcFSPassD->pcFSStdD[ iter ]->stdNum << END_OF_MESSAGE;
                DMSG( -diagLvl ) << "@@Max@@,force_bnd_env =  "<< pcFSPassD->pcPEnvD->force_bnd_env[ maxl ] << ",std No=" <<pcFSPassD->pcFSStdD[ iter ]->stdNum << END_OF_MESSAGE;

                //----------------------------------------------------------
                // Calculate the minimum roll bending force component of the
                // envelope for the given conditions.
                //----------------------------------------------------------
                line_num = __LINE__;
                pcFSPassD->pcFSStdD[ iter ]->pcUFDD->Bnd_Frc (
                             ufd_pu_prf * pcFSPassD->pcFSStdD[ iter ]->pcExPceD->thick,
                             pcFSPassD->pcPEnvD->force_pu_wid_env [ minl ],
                             pcFSPassD->pcPEnvD->pce_wr_crn_env   [ minl ],
                             pcFSPassD->pcPEnvD->wr_br_crn_env    [ minl ],
                             pcFSPassD->pcFSStdD[ iter ]->force_bnd_lim,
                             pcFSPassD->pcPEnvD->force_bnd_env    [ minl ],
                             force_bnd_des );

                DMSG( -diagLvl ) << "@@Min@@,force_bnd_env =  "<< pcFSPassD->pcPEnvD->force_bnd_env[ minl ] << ",std No=" <<pcFSPassD->pcFSStdD[ iter ]->stdNum << END_OF_MESSAGE;
                DMSG( -diagLvl ) << "@@Max@@,force_bnd_env =  "<< pcFSPassD->pcPEnvD->force_bnd_env[ maxl ] << ",std No=" <<pcFSPassD->pcFSStdD[ iter ]->stdNum << END_OF_MESSAGE;

                force_bnd_clmp =
                    force_bnd_des != pcFSPassD->pcPEnvD->force_bnd_env[ minl ];

                //-----------------------------------------------------------------
                // Calculate the minimum UFD roll gap per unit profile component of
                // the envelope for the given conditions.
                //-----------------------------------------------------------------
                line_num = __LINE__;
                pcFSPassD->pcPEnvD->ufd_pu_prf_env[ minl ] =
                    pcFSPassD->pcFSStdD[ iter ]->pcUFDD->Prf(
                             pcFSPassD->pcPEnvD->force_pu_wid_env [ minl ],
                             pcFSPassD->pcPEnvD->force_bnd_env    [ minl ],
                             pcFSPassD->pcPEnvD->pce_wr_crn_env   [ minl ],
                             pcFSPassD->pcPEnvD->wr_br_crn_env    [ minl ] ) /
                    pcFSPassD->pcFSStdD[ iter ]->pcExPceD->thick;

                if ( force_bnd_clmp &&
                     pcFSPassD->pcFSStdD[ iter ]->pcLRGD->pce_infl_cof >
                         pcFSPassD->pcPEnvD->pcPEnv->pce_infl_cof_mn )
                {
                    force_bnd_clmp = false;

                    //-------------------------------------------------------------
                    // Calculate the desired effective entry per unit profile for
                    // the given conditions.
                    //-------------------------------------------------------------
                    line_num = __LINE__;
                    ef_en_pu_prf =
                        pcFSPassD->pcFSStdD[ iter ]->pcLRGD->Ef_En_PU_Prf3 (
                                   pcFSPassD->pcLPceD->strn_rlf_cof,
                                   pcFSPassD->pcPEnvD->ufd_pu_prf_env [ minl ],
                                   ef_ex_pu_prf                             );

                    //------------------------------------------------------------
                    // Restrict the effective entry per unit profile to within the
                    // effective per unit profile envelope.
                    //------------------------------------------------------------
                    ef_en_pu_prf_buf =
                        cMathUty::Clamp( ef_en_pu_prf,
                                         pcFSPassD->pcPrvAct->pcPEnvD->ef_pu_prf_env[ minl ],
                                         pcFSPassD->pcPrvAct->pcPEnvD->ef_pu_prf_env[ maxl ] );

                    //---------------------------------------------------------
                    // Indicate that a move should be made to the previous non-
                    // dummied pass if an effective per unit profile change is
                    // possible.
                    //---------------------------------------------------------
                    line_num = __LINE__;
                    move_prv[ minl ] =
                        move_prv[ minl ] ||
                        ( ef_en_pu_prf_buf !=
                              pcFSPassD->pcPrvAct->pcPEnvD->ef_pu_prf_lim[ minl ] &&
                          pcFSPassD->pcPrvAct->pcPEnvD->ef_pu_prf_env[ minl ] !=
                              pcFSPassD->pcPrvAct->pcPEnvD->ef_pu_prf_env[ maxl ] );

                    //------------------------------------------------------------
                    // Capture the minimum effective entry per unit profile limit.
                    //------------------------------------------------------------
                    pcFSPassD->pcPrvAct->pcPEnvD->ef_pu_prf_lim[ minl ] =
                        ef_en_pu_prf_buf;
                }
            }
            // if not going to previous pass calculations
            if ( !move_prv[ minl ] )
            {
                //----------------------------------------------
                // Calculate the stand exit differential strain.
                //----------------------------------------------
                line_num = __LINE__;
                std_ex_strn =
                    pcFSPassD->pcFSStdD[ iter ]->pcLRGD->Std_Ex_Strn1 (
                               pcFSPassD->pcPrvAct->pcPEnvD->ef_pu_prf_env [ minl ],
                               pcFSPassD->pcPEnvD->ufd_pu_prf_env          [ minl ] );

                // was profile reduced too much
//@2ND(M16M062)_b begin
                //if ( std_ex_strn < pcFSPassD->pcPEnvD->std_ex_strn_lim[ cb ] )
                if ( 1 < 0 )
//@2ND(M16M062)_b end
                {
                    //------------------------------------------------------------
                    // Select a higher rolling force per unit piece width by using
                    // the piece critical buckling limit for a center buckle
                    // flatness defect.
                    //------------------------------------------------------------
                    line_num = __LINE__;
                    ufd_pu_prf =
                        pcFSPassD->pcFSStdD[ iter ]->pcLRGD->UFD_PU_Prf1 (
                             pcFSPassD->pcPrvAct->pcPEnvD->ef_pu_prf_env[ minl ],
                             pcFSPassD->pcPEnvD->std_ex_strn_lim[ cb ]   );

                    //---------------------------------------------------------
                    // Calculate the rolling force per unit piece for the given
                    // conditions.
                    //---------------------------------------------------------
                    line_num = __LINE__;
                    pcFSPassD->pcFSStdD[ iter ]->pcUFDD->Frc_PU_Wid(
                                    ufd_pu_prf * pcFSPassD->pcFSStdD[ iter ]->pcExPceD->thick,
                                    pcFSPassD->pcPEnvD->force_bnd_env  [ minl ],
                                    pcFSPassD->pcPEnvD->pce_wr_crn_env [ minl ],
                                    pcFSPassD->pcPEnvD->wr_br_crn_env  [ minl ],
                                    force_pu_wid_buf,
                                    ufdd_status );

                    if ( ufdd_status != cUFDD::valid )
                    {
                        DMSG( diagLvl )
                            << "Calculate: PID="
                            << pcFSPassD->pcExPceD[ iter ]->pcPce->prod_id
                            << ", UFDD Frc_PU_Wid status="
                            << cUFDD::Image( ufdd_status )
                            << END_OF_MESSAGE;

                        // set defired force to anextreme value NORMALLY positive
                        force_pu_wid_buf =
                                pcFSPassD->pcPEnvD->force_pu_wid_lim[ maxl ] + 10.0F;
                        if ( pcFSPassD->pcPEnvD->dprf_dfrcw < 0.0 )
                        {
                            force_pu_wid_buf =
                                pcFSPassD->pcPEnvD->force_pu_wid_lim[ minl ] - 10.0F;
                        }
                    }
                    //----------------------------------------------------------
                    // Restrict the minimum rolling force per unit piece width
                    // component of the envelope to within the rolling force per
                    // unit piece width limits.
                    //----------------------------------------------------------
                    line_num = __LINE__;
                    pcFSPassD->pcPEnvD->force_pu_wid_env[ minl ] =
                        cMathUty::Clamp( force_pu_wid_buf,
                                         pcFSPassD->pcPEnvD->force_pu_wid_lim[ minl ],
                                         pcFSPassD->pcPEnvD->force_pu_wid_lim[ maxl ] );

                    // if the force was clamped
                    if ( pcFSPassD->pcPEnvD->force_pu_wid_env[ minl ] != force_pu_wid_buf )
                    {
                        //----------------------------------------------------
                        // Calculate the work roll crown change and adjust the
                        // minimum piece to work roll and minimum work roll to
                        // backup roll stack crown envelope components.
                        //----------------------------------------------------
                        line_num = __LINE__;
                        pcFSPassD->pcFSStdD[ iter ]->pcUFDD->Crns(
                                  ufd_pu_prf * pcFSPassD->pcFSStdD[ iter ]->pcExPceD->thick,
                                  pcFSPassD->pcPEnvD->force_pu_wid_env[ minl ],
                                  pcFSPassD->pcPEnvD->force_bnd_env[ minl ],
                                  pce_wr_crn,
                                  wr_br_crn );

                        //-------------------------------------------------------
                        // Calculate the minimum roll shift position component of
                        // the envelope for the given conditions.
                        //-------------------------------------------------------
                        line_num = __LINE__;
                DMSG( -diagLvl ) << "@@Min@@,pos_shft_env =  "<< pcFSPassD->pcPEnvD->pos_shft_env[ minl ] << ",std No=" <<pcFSPassD->pcFSStdD[ iter ]->stdNum << END_OF_MESSAGE;
                DMSG( -diagLvl ) << "@@Max@@,pos_shft_env =  "<< pcFSPassD->pcPEnvD->pos_shft_env[ maxl ] << ",std No=" <<pcFSPassD->pcFSStdD[ iter ]->stdNum << END_OF_MESSAGE;

                        pcFSPassD->pcFSStdD[ iter ]->pcCRLCD->Shft_Pos(
                                      pce_wr_crn,
                                      pcFSPassD->pcPEnvD->angl_pc_env  [ minl ],
                                      pcFSPassD->pcFSStdD[ iter ]->wr_shft_lim,
                                      pcFSPassD->pcPEnvD->pos_shft_env [ minl ],
                                      crlcd_status );

                DMSG( -diagLvl ) << "@@Min@@,pos_shft_env =  "<< pcFSPassD->pcPEnvD->pos_shft_env[ minl ] << ",std No=" <<pcFSPassD->pcFSStdD[ iter ]->stdNum << END_OF_MESSAGE;
                DMSG( -diagLvl ) << "@@Max@@,pos_shft_env =  "<< pcFSPassD->pcPEnvD->pos_shft_env[ maxl ] << ",std No=" <<pcFSPassD->pcFSStdD[ iter ]->stdNum << END_OF_MESSAGE;

                        if ( crlcd_status != cCRLCD::valid )
                        {
                            DMSG( diagLvl )
                                << "Calculate: PID="
                                << pcFSPassD->pcExPceD[ iter ]->pcPce->prod_id
                                << ",CRLCD Crns status="
                                << cCRLCD::Image( crlcd_status )
                                << END_OF_MESSAGE;
                        }
                        //------------------------------------------------------------------
                        // Re-calculate the following composite roll stack crown quantities:
                        //     Piece to work roll stack crown
                        //     Work roll to backup roll stack crown
                        //------------------------------------------------------------------
                        line_num = __LINE__;
                        pcFSPassD->pcFSStdD[ iter ]->pcCRLCD->Crns(
                                  pcFSPassD->pcPEnvD->pos_shft_env  [ minl ],
                                  pcFSPassD->pcPEnvD->angl_pc_env   [ minl ],
                                  pcFSPassD->pcPEnvD->pce_wr_crn_env[ minl ],
                                  pcFSPassD->pcPEnvD->wr_br_crn_env [ minl ] );

                DMSG( -diagLvl ) << "@@Min@@,pos_shft_env =  "<< pcFSPassD->pcPEnvD->pos_shft_env[ minl ] << ",std No=" <<pcFSPassD->pcFSStdD[ iter ]->stdNum << END_OF_MESSAGE;
                DMSG( -diagLvl ) << "@@Max@@,pos_shft_env =  "<< pcFSPassD->pcPEnvD->pos_shft_env[ maxl ] << ",std No=" <<pcFSPassD->pcFSStdD[ iter ]->stdNum << END_OF_MESSAGE;

                        //-----------------------------------------------------
                        // Calculate the minimum piece to work roll stack crown
                        // envelope component.
                        //-----------------------------------------------------
                        line_num = __LINE__;
                        pce_wr_crn =
                            pcFSPassD->pcFSStdD[ iter ]->pcUFDD->Pce_WR_Crn(
                                        ufd_pu_prf * pcFSPassD->pcFSStdD[ iter ]->pcExPceD->thick,
                                        pcFSPassD->pcPEnvD->force_pu_wid_env[ minl ],
                                        pcFSPassD->pcPEnvD->force_bnd_env[ minl ],
                                        pcFSPassD->pcPEnvD->wr_br_crn_env[ minl ] );

                        //--------------------------------------------------------
                        // Calculate the minimum pair cross angle component of the
                        // envelope for the given conditions.
                        //--------------------------------------------------------
                        line_num = __LINE__;
                        pcFSPassD->pcFSStdD[ iter ]->pcCRLCD->PC_Angl (
                                     pce_wr_crn,
                                     pcFSPassD->pcPEnvD->angl_pc_env[ minl ],
                                     pcFSPassD->pcFSStdD[ iter ]->angl_pc_lim );

                        //------------------------------------------------------
                        // Re-calculate the following composite roll stack crown
                        // quantities:
                        //     Piece to work roll stack crown
                        //     Work roll to backup roll stack crown
                        //------------------------------------------------------
                        line_num = __LINE__;
                        pcFSPassD->pcFSStdD[ iter ]->pcCRLCD->Crns(
                                  pcFSPassD->pcPEnvD->pos_shft_env  [ minl ],
                                  pcFSPassD->pcPEnvD->angl_pc_env   [ minl ],
                                  pcFSPassD->pcPEnvD->pce_wr_crn_env[ minl ],
                                  pcFSPassD->pcPEnvD->wr_br_crn_env [ minl ] );

                DMSG( -diagLvl ) << "@@Min@@,pos_shft_env =  "<< pcFSPassD->pcPEnvD->pos_shft_env[ minl ] << ",std No=" <<pcFSPassD->pcFSStdD[ iter ]->stdNum << END_OF_MESSAGE;
                DMSG( -diagLvl ) << "@@Max@@,pos_shft_env =  "<< pcFSPassD->pcPEnvD->pos_shft_env[ maxl ] << ",std No=" <<pcFSPassD->pcFSStdD[ iter ]->stdNum << END_OF_MESSAGE;

                        //----------------------------------------------------------
                        // Calculate the minimum roll bending force component of the
                        // envelope for the given conditions.
                        //----------------------------------------------------------
                        line_num = __LINE__;
                        pcFSPassD->pcFSStdD[ iter ]->pcUFDD->Bnd_Frc(
                                     ufd_pu_prf * pcFSPassD->pcFSStdD[ iter ]->pcExPceD->thick,
                                     pcFSPassD->pcPEnvD->force_pu_wid_env [ minl ],
                                     pcFSPassD->pcPEnvD->pce_wr_crn_env   [ minl ],
                                     pcFSPassD->pcPEnvD->wr_br_crn_env    [ minl ],
                                     pcFSPassD->pcFSStdD[ iter ]->force_bnd_lim,
                                     pcFSPassD->pcPEnvD->force_bnd_env    [ minl ],
                                     force_bnd_des );

                        //---------------------------------------------------------
                        // Capture the current pass being evaluated as the limiting
                        // pass for the minimum component of the envelope.
                        //---------------------------------------------------------
                        if ( pas_env_lim[ minl ] == 0 )
                        {
                            pas_env_lim[ minl ] = pcFSPassD->pcPass->num;
                        }
                    }
                    //--------------------------------------------------------------
                    // Calculate the minimum UFD roll gap per unit profile component
                    // of the envelope for the given conditions.
                    //--------------------------------------------------------------
                    line_num = __LINE__;
                    pcFSPassD->pcPEnvD->ufd_pu_prf_env[ minl ] =
                        pcFSPassD->pcFSStdD[ iter ]->pcUFDD->Prf(
                                 pcFSPassD->pcPEnvD->force_pu_wid_env [ minl ],
                                 pcFSPassD->pcPEnvD->force_bnd_env    [ minl ],
                                 pcFSPassD->pcPEnvD->pce_wr_crn_env   [ minl ],
                                 pcFSPassD->pcPEnvD->wr_br_crn_env    [ minl ] ) /
                        pcFSPassD->pcFSStdD[ iter ]->pcExPceD->thick;
                }
                // strain too high (due to low entry profile)
//@2ND(M16M062)_b begin
                //if ( std_ex_strn > pcFSPassD->pcPEnvD->std_ex_strn_lim[ we ] &&
                if ( 0 > 1 &&
//@2ND(M16M062)_b end
                     pcFSPassD->pcFSStdD[ iter ]->pcLRGD->pce_infl_cof >
                         pcFSPassD->pcPEnvD->pcPEnv->pce_infl_cof_mn )
                {
                    //--------------------------------------------------------------
                    // Select a higher composite roll stack crown by using the piece
                    // critical buckling limit for a wavy edge flatness defect.
                    //--------------------------------------------------------------
                    line_num = __LINE__;
                    ufd_pu_prf =
                        pcFSPassD->pcFSStdD[ iter ]->pcLRGD->UFD_PU_Prf1 (
                                   pcFSPassD->pcPrvAct->pcPEnvD->ef_pu_prf_env[ minl ],
                                   pcFSPassD->pcPEnvD->std_ex_strn_lim [ we ] );

                    //--------------------------------------------------------------
                    // Calculate the work roll crown change and adjust the minimum
                    // piece to work roll and minimum work roll to backup roll stack
                    // crown envelope components.
                    //--------------------------------------------------------------
                    line_num = __LINE__;
                    pcFSPassD->pcFSStdD[ iter ]->pcUFDD->Crns (
                              ufd_pu_prf * pcFSPassD->pcFSStdD[ iter ]->pcExPceD->thick,
                              pcFSPassD->pcPEnvD->force_pu_wid_env [ minl ],
                              pcFSPassD->pcPEnvD->force_bnd_env    [ minl ],
                              pce_wr_crn,
                              wr_br_crn );

                    //-----------------------------------------------------------
                    // Calculate the minimum roll shift position component of the
                    // envelope for the given conditions.
                    //-----------------------------------------------------------
                    line_num = __LINE__;
                    pcFSPassD->pcFSStdD[ iter ]->pcCRLCD->Shft_Pos(
                                  pce_wr_crn,
                                  pcFSPassD->pcPEnvD->angl_pc_env [ minl ],
                                  pcFSPassD->pcFSStdD[ iter ]->wr_shft_lim,
                                  pcFSPassD->pcPEnvD->pos_shft_env[ minl ],
                                  crlcd_status );

                DMSG( -diagLvl ) << "@@Min@@,pos_shft_env =  "<< pcFSPassD->pcPEnvD->pos_shft_env[ minl ] << ",std No=" <<pcFSPassD->pcFSStdD[ iter ]->stdNum << END_OF_MESSAGE;
                DMSG( -diagLvl ) << "@@Max@@,pos_shft_env =  "<< pcFSPassD->pcPEnvD->pos_shft_env[ maxl ] << ",std No=" <<pcFSPassD->pcFSStdD[ iter ]->stdNum << END_OF_MESSAGE;

                    if ( crlcd_status != cCRLCD::valid )
                    {
                        DMSG( diagLvl )
                            << "Calculate: PID="
                            << pcFSPassD->pcExPceD[ iter ]->pcPce->prod_id
                            << ", CRLCD Crns status="
                            << cCRLCD::Image( crlcd_status )
                            << END_OF_MESSAGE;
                    }
                    //------------------------------------------------------------------
                    // Re-calculate the following composite roll stack crown quantities:
                    //     Piece to work roll stack crown
                    //     Work roll to backup roll stack crown
                    //------------------------------------------------------------------
                    line_num = __LINE__;
                    pcFSPassD->pcFSStdD[ iter ]->pcCRLCD->Crns(
                              pcFSPassD->pcPEnvD->pos_shft_env  [ minl ],
                              pcFSPassD->pcPEnvD->angl_pc_env   [ minl ],
                              pcFSPassD->pcPEnvD->pce_wr_crn_env[ minl ],
                              pcFSPassD->pcPEnvD->wr_br_crn_env [ minl ] );

                DMSG( -diagLvl ) << "@@Min@@,pos_shft_env =  "<< pcFSPassD->pcPEnvD->pos_shft_env[ minl ] << ",std No=" <<pcFSPassD->pcFSStdD[ iter ]->stdNum << END_OF_MESSAGE;
                DMSG( -diagLvl ) << "@@Max@@,pos_shft_env =  "<< pcFSPassD->pcPEnvD->pos_shft_env[ maxl ] << ",std No=" <<pcFSPassD->pcFSStdD[ iter ]->stdNum << END_OF_MESSAGE;

                    //--------------------------------------------------------------
                    // Calculate the minimum piece to work roll stack crown envelope
                    // component.
                    //--------------------------------------------------------------
                    line_num = __LINE__;
                    pce_wr_crn =
                        pcFSPassD->pcFSStdD[ iter ]->pcUFDD->Pce_WR_Crn(
                                   ufd_pu_prf * pcFSPassD->pcFSStdD[ iter ]->pcExPceD->thick,
                                   pcFSPassD->pcPEnvD->force_pu_wid_env[ minl ],
                                   pcFSPassD->pcPEnvD->force_bnd_env   [ minl ],
                                   pcFSPassD->pcPEnvD->wr_br_crn_env   [ minl ] );

                    //--------------------------------------------------------
                    // Calculate the minimum pair cross angle component of the
                    // envelope for the given conditions.
                    //--------------------------------------------------------
                    line_num = __LINE__;
                    pcFSPassD->pcFSStdD[ iter ]->pcCRLCD->PC_Angl(
                                 pce_wr_crn,
                                 pcFSPassD->pcPEnvD->angl_pc_env[ minl ],
                                 pcFSPassD->pcFSStdD[ iter ]->angl_pc_lim );

                    //------------------------------------------------------
                    // Re-calculate the following composite roll stack crown
                    // quantities:
                    //     Piece to work roll stack crown
                    //     Work roll to backup roll stack crown
                    //------------------------------------------------------
                    line_num = __LINE__;
                    pcFSPassD->pcFSStdD[ iter ]->pcCRLCD->Crns(
                              pcFSPassD->pcPEnvD->pos_shft_env  [ minl ],
                              pcFSPassD->pcPEnvD->angl_pc_env   [ minl ],
                              pcFSPassD->pcPEnvD->pce_wr_crn_env[ minl ],
                              pcFSPassD->pcPEnvD->wr_br_crn_env [ minl ] );

                DMSG( -diagLvl ) << "@@Min@@,pos_shft_env =  "<< pcFSPassD->pcPEnvD->pos_shft_env[ minl ] << ",std No=" <<pcFSPassD->pcFSStdD[ iter ]->stdNum << END_OF_MESSAGE;
                DMSG( -diagLvl ) << "@@Max@@,pos_shft_env =  "<< pcFSPassD->pcPEnvD->pos_shft_env[ maxl ] << ",std No=" <<pcFSPassD->pcFSStdD[ iter ]->stdNum << END_OF_MESSAGE;

                    //----------------------------------------------------------
                    // Calculate the minimum roll bending force component of the
                    // envelope for the given conditions.
                    //----------------------------------------------------------
                    line_num = __LINE__;
                    pcFSPassD->pcFSStdD[ iter ]->pcUFDD->Bnd_Frc(
                                 ufd_pu_prf * pcFSPassD->pcFSStdD[ iter ]->pcExPceD->thick,
                                 pcFSPassD->pcPEnvD->force_pu_wid_env [ minl ],
                                 pcFSPassD->pcPEnvD->pce_wr_crn_env   [ minl ],
                                 pcFSPassD->pcPEnvD->wr_br_crn_env    [ minl ],
                                 pcFSPassD->pcFSStdD[ iter ]->force_bnd_lim,
                                 pcFSPassD->pcPEnvD->force_bnd_env    [ minl ],
                                 force_bnd_des );

                        force_bnd_clmp =
                            force_bnd_des != pcFSPassD->pcPEnvD->force_bnd_env[ minl ];

                    if ( force_bnd_clmp )
                    {
                        force_bnd_clmp = false;

                        //---------------------------------------------------
                        // Select a lower rolling force per unit piece width.
                        //---------------------------------------------------
                        line_num = __LINE__;
                        pcFSPassD->pcFSStdD[ iter ]->pcUFDD->Frc_PU_Wid (
                            ufd_pu_prf * pcFSPassD->pcFSStdD[ iter ]->pcExPceD->thick,
                            pcFSPassD->pcPEnvD->force_bnd_env  [ minl ],
                            pcFSPassD->pcPEnvD->pce_wr_crn_env [ minl ],
                            pcFSPassD->pcPEnvD->wr_br_crn_env  [ minl ],
                            force_pu_wid_buf,
                            ufdd_status );

                        if ( ufdd_status != cUFDD::valid )
                        {
                            DMSG( diagLvl )
                                << "Calculate: PID="
                                << pcFSPassD->pcExPceD[ iter ]->pcPce->prod_id
                                << ",UFDD Frc_PU_Wid status="
                                << cUFDD::Image(ufdd_status)
                                << END_OF_MESSAGE;

                            // set desired force to an extreme value NORMALLY positive
                            force_pu_wid_buf =
                                pcFSPassD->pcPEnvD->force_pu_wid_lim[ maxl ]   + 10.0F;
                            if ( pcFSPassD->pcPEnvD->dprf_dfrcw < 0.0F )
                            {
                                force_pu_wid_buf =
                                  pcFSPassD->pcPEnvD->force_pu_wid_lim[ minl ] - 10.0F;
                            }
                        }
                            //----------------------------------------------------------
                        // Restrict the minimum rolling force per unit piece width
                        // component of the envelope to within the rolling force per
                        // unit piece width limits.
                        //----------------------------------------------------------
                        line_num = __LINE__;
                        pcFSPassD->pcPEnvD->force_pu_wid_env[ minl ] =
                            cMathUty::Clamp( force_pu_wid_buf,
                                             pcFSPassD->pcPEnvD->force_pu_wid_lim[ minl ],
                                             pcFSPassD->pcPEnvD->force_pu_wid_lim[ maxl ] );

                        //--------------------------------------------------------
                        // Indicate that the required rolling force per unit piece
                        // width change was restricted.
                        //--------------------------------------------------------
                        force_chg_clmp =
                            pcFSPassD->pcPEnvD->force_pu_wid_env[ minl ] != force_pu_wid_buf;
                    }
                    //--------------------------------------------------------------
                    // Calculate the minimum UFD roll gap per unit profile component
                    // of the envelope for the given conditions.
                    //--------------------------------------------------------------
                    line_num = __LINE__;
                    pcFSPassD->pcPEnvD->ufd_pu_prf_env[ minl ] =
                        pcFSPassD->pcFSStdD[ iter ]->pcUFDD->Prf(
                                 pcFSPassD->pcPEnvD->force_pu_wid_env[ minl ],
                                 pcFSPassD->pcPEnvD->force_bnd_env   [ minl ],
                                 pcFSPassD->pcPEnvD->pce_wr_crn_env  [ minl ],
                                 pcFSPassD->pcPEnvD->wr_br_crn_env   [ minl ] ) /
                        pcFSPassD->pcFSStdD[ iter ]->pcExPceD->thick;

                    if ( force_chg_clmp )
                    {
                        force_chg_clmp = false;

                        //--------------------------------------------------------
                        // Attempt to change the effective entry per unit profile.
                        // This will not help the current pass rolling force per
                        // unit piece width, but may change the previous pass
                        // rolling force per unit piece width.  Use the piece
                        // critical buckling limit for a wavy edge flatness defect
                        // as a possible starting point.
                        //--------------------------------------------------------
                        line_num = __LINE__;
                        ef_en_pu_prf =
                            pcFSPassD->pcFSStdD[ iter ]->pcLRGD->Ef_En_PU_Prf1 (
                                 pcFSPassD->pcPEnvD->ufd_pu_prf_env [ minl ],
                                 pcFSPassD->pcPEnvD->std_ex_strn_lim [ we ]    );

                        //--------------------------------------------------------
                        // Restrict the effective entry per unit profile to within
                        // the effective per unit profile envelope.
                        //--------------------------------------------------------
                        line_num = __LINE__;
                        ef_en_pu_prf_buf =
                            cMathUty::Clamp( ef_en_pu_prf,
                                             pcFSPassD->pcPrvAct->pcPEnvD->ef_pu_prf_env [ minl ],
                                             pcFSPassD->pcPrvAct->pcPEnvD->ef_pu_prf_env [ maxl ] );

                        //---------------------------------------------------------
                        // Indicate that a move should be made to the previous non-
                        // dummied pass if an effective per unit profile change is
                        // possible.
                        //---------------------------------------------------------
                        line_num = __LINE__;
                        move_prv[ minl ] =
                            ( ef_en_pu_prf != pcFSPassD->pcPrvAct->pcPEnvD->ef_pu_prf_env[ minl ] ) &&
                            ( pcFSPassD->pcPrvAct->pcPEnvD->ef_pu_prf_env[ minl ] !=
                                pcFSPassD->pcPrvAct->pcPEnvD->ef_pu_prf_env[ maxl ] );

                        pcFSPassD->pcPrvAct->pcPEnvD->ef_pu_prf_lim[ minl ] =
                            ef_en_pu_prf;
                    }
                }
            }
            //------------------------------------------------------------------
            // Calculate the minimum effective per unit profile component of the
            // envelope for the given conditions.
            //------------------------------------------------------------------
            line_num = __LINE__;

            DMSG( -diagLvl ) << "@@Min@@,ef_pu_prf_env =  "<< pcFSPassD->pcPEnvD->ef_pu_prf_env[ minl ] << ",std No=" <<pcFSPassD->pcFSStdD[ iter ]->stdNum << END_OF_MESSAGE;

            pcFSPassD->pcPEnvD->ef_pu_prf_env[ minl ] =
                pcFSPassD->pcFSStdD[ iter ]->pcLRGD->Ef_Ex_PU_Prf3(
                           pcFSPassD->pcLPceD->strn_rlf_cof,
                           pcFSPassD->pcPrvAct->pcPEnvD->ef_pu_prf_env[ minl ],
                           pcFSPassD->pcPEnvD->ufd_pu_prf_env         [ minl ] );

            DMSG( -diagLvl ) << "@@Min@@,ef_pu_prf_env =  "<< pcFSPassD->pcPEnvD->ef_pu_prf_env[ minl ] << ",std No=" <<pcFSPassD->pcFSStdD[ iter ]->stdNum << END_OF_MESSAGE;

            //*******************************************************
            // DETERMINE THE MAXIMUM ENVELOPE COMPONENTS:
            //     Effective exit per unit profile.
            //     UFD roll gap per unit profile
            //     Rolling force per unit piece width
            //-------------------------------------------------------
            move_prv[ maxl ] = false;
//DMSG(-diagLvl) << "Deng gsm test: PEnvD::Calculate !" << END_OF_MESSAGE;

            //------------------------------------------------------------------
            // Calculate the maximum effective per unit profile component of the
            // envelope for the given conditions.
            //------------------------------------------------------------------
            line_num = __LINE__;

            DMSG( -diagLvl ) << "@@maxl@@,ef_pu_prf_env      =  "<< pcFSPassD->pcPEnvD->ef_pu_prf_env[ maxl ] << ",std No=" <<pcFSPassD->pcFSStdD[ iter ]->stdNum << END_OF_MESSAGE;

            pcFSPassD->pcPEnvD->ef_pu_prf_env[ maxl ] =
                pcFSPassD->pcFSStdD[ iter ]->pcLRGD->Ef_Ex_PU_Prf3 (
                               pcFSPassD->pcLPceD->strn_rlf_cof,
                               pcFSPassD->pcPrvAct->pcPEnvD->ef_pu_prf_env [ maxl ],
                               pcFSPassD->pcPEnvD->ufd_pu_prf_env          [ maxl ] );

            //DMSG( -diagLvl ) << "@@maxl@@,strn_rlf_cof   =  "<< pcFSPassD->pcLPceD->strn_rlf_cof << ",std No=" <<pcFSPassD->pcFSStdD[ iter ]->stdNum << END_OF_MESSAGE;
            //DMSG( -diagLvl ) << "@@maxl@@,ef_pu_prf_env  =  "<< pcFSPassD->pcPrvAct->pcPEnvD->ef_pu_prf_env[ maxl ] << ",std No=" <<pcFSPassD->pcFSStdD[ iter ]->stdNum << END_OF_MESSAGE;
            //DMSG( -diagLvl ) << "@@maxl@@,ufd_pu_prf_env =  "<< pcFSPassD->pcPEnvD->ef_pu_prf_env[ maxl ] << ",std No=" <<pcFSPassD->pcFSStdD[ iter ]->stdNum << END_OF_MESSAGE;
            //DMSG( -diagLvl ) << "@@maxl@@,ef_pu_prf_env  =  "<< pcFSPassD->pcPEnvD->ufd_pu_prf_env[ maxl ] << ",std No=" <<pcFSPassD->pcFSStdD[ iter ]->stdNum << END_OF_MESSAGE;
            //DMSG( -diagLvl ) << "@@maxl@@,ef_pu_prf_lim  =  "<< pcFSPassD->pcPEnvD->ef_pu_prf_lim [ maxl ] << ",std No=" <<pcFSPassD->pcFSStdD[ iter ]->stdNum << END_OF_MESSAGE;
            DMSG( -diagLvl ) << "@@maxl@@,strn_rlf_cof       =  "<< pcFSPassD->pcLPceD->strn_rlf_cof << ",std No=" <<pcFSPassD->pcFSStdD[ iter ]->stdNum << END_OF_MESSAGE;
            DMSG( -diagLvl ) << "@@maxl@@,pce_infl_cof       =  "<<pcFSPassD->pcFSStdD[ iter ]->pcLRGD->pce_infl_cof << ",std No=" <<pcFSPassD->pcFSStdD[ iter ]->stdNum << END_OF_MESSAGE;
            //DMSG( -diagLvl ) << "@@maxl@@,prf_recv_cof       =  "<<pcFSPassD->pcFSStdD[ iter ]->pcLRGD->pcLRG->prf_recv_cof << ",std No=" <<pcFSPassD->pcFSStdD[ iter ]->stdNum << END_OF_MESSAGE;
            DMSG( -diagLvl ) << "@@maxl@@,prf_chg_attn_fac   =  "<<pcFSPassD->pcFSStdD[ iter ]->pcLRGD->prf_chg_attn_fac << ",std No=" <<pcFSPassD->pcFSStdD[ iter ]->stdNum << END_OF_MESSAGE;

            DMSG( -diagLvl ) << "@@maxl@@,ef_pu_prf_env_p    =  "<< pcFSPassD->pcPrvAct->pcPEnvD->ef_pu_prf_env[ maxl ] << ",std No=" <<pcFSPassD->pcFSStdD[ iter ]->stdNum << END_OF_MESSAGE;
            DMSG( -diagLvl ) << "@@maxl@@,ef_pu_prf_env      =  "<< pcFSPassD->pcPEnvD->ef_pu_prf_env[ maxl ] << ",std No=" <<pcFSPassD->pcFSStdD[ iter ]->stdNum << END_OF_MESSAGE;
            DMSG( -diagLvl ) << "@@maxl@@,ufd_pu_prf_env     =  "<< pcFSPassD->pcPEnvD->ufd_pu_prf_env[ maxl ] << ",std No=" <<pcFSPassD->pcFSStdD[ iter ]->stdNum << END_OF_MESSAGE;
            DMSG( -diagLvl ) << "@@maxl@@,ef_pu_prf_lim      =  "<< pcFSPassD->pcPEnvD->ef_pu_prf_lim [ maxl ] << ",std No=" <<pcFSPassD->pcFSStdD[ iter ]->stdNum << END_OF_MESSAGE;

            if ( pcFSPassD->pcPEnvD->ef_pu_prf_env[ maxl ] >
                     pcFSPassD->pcPEnvD->ef_pu_prf_lim[ maxl ] )
            {

            DMSG( -1 ) << "@@maxl@@,ef_pu_prf_env    =  "<< pcFSPassD->pcPEnvD->ef_pu_prf_env[ maxl ] << ",std No=" <<pcFSPassD->pcFSStdD[ iter ]->stdNum << END_OF_MESSAGE;
            DMSG( -1 ) << "@@maxl@@,ef_pu_prf_lim    =  "<< pcFSPassD->pcPEnvD->ef_pu_prf_lim[ maxl ] << ",std No=" <<pcFSPassD->pcFSStdD[ iter ]->stdNum << END_OF_MESSAGE;

                if ( pcFSPassD != pcLstActFSPassD &&
                     pcFSPassD->pcNxtAct->pcPEnvD->pce_wr_crn_env[ maxl ] ==
                         pcFSPassD->pcNxtAct->pcPEnvD->pce_wr_crn_lim[ minl ] &&
                     pcFSPassD->pcNxtAct->pcPEnvD->wr_br_crn_env[ maxl ] ==
                         pcFSPassD->pcNxtAct->pcPEnvD->wr_br_crn_lim[ minl ] &&
                     pcFSPassD->pcNxtAct->pcPEnvD->force_bnd_env[ maxl ] ==
                         pcFSPassD->pcNxtAct->pcFSStdD[ iter ]->force_bnd_lim[ minl ] )
                {
                    //-------------------------------------------------------------
                    // The highest pass encountered is defined as the limiting pass
                    // with respect to the effective per unit crown envelope.
                    //-------------------------------------------------------------
                    line_num = __LINE__;
                    pas_env_lim[ maxl ] =
                        cMathUty::Max( pcFSPassD->pcNxtAct->pcPass->num,
                                       pas_env_lim[ maxl ] );
                }
                ef_ex_pu_prf = pcFSPassD->pcPEnvD->ef_pu_prf_lim[ maxl ];

                //----------------------------------------------------------
                // Calculate the UFD roll gap per unit profile for the given
                // conditions.
                //----------------------------------------------------------
                line_num = __LINE__;
                ufd_pu_prf =
                    pcFSPassD->pcFSStdD[ iter ]->pcLRGD->UFD_PU_Prf3 (
                               pcFSPassD->pcLPceD->strn_rlf_cof,
                               pcFSPassD->pcPrvAct->pcPEnvD->ef_pu_prf_env[ maxl ],
                               ef_ex_pu_prf                          );

                // if desired ufd = ef exit it was not possible to change ufd
                ufdd_status = cUFDD::undef;
                if ( ufd_pu_prf != ef_ex_pu_prf )
                {
                    //---------------------------------------------------
                    // Select a lower rolling force per unit piece width.
                    //---------------------------------------------------
                    line_num = __LINE__;
                    pcFSPassD->pcFSStdD[ iter ]->pcUFDD->Frc_PU_Wid(
                                    ufd_pu_prf * pcFSPassD->pcFSStdD[ iter ]->pcExPceD->thick,
                                    pcFSPassD->pcPEnvD->force_bnd_env [ maxl ],
                                    pcFSPassD->pcPEnvD->pce_wr_crn_env[ maxl ],
                                    pcFSPassD->pcPEnvD->wr_br_crn_env [ maxl ],
                                    force_pu_wid_buf,
                                    ufdd_status );

                    if ( ufdd_status != cUFDD::valid )
                    {
                        DMSG( diagLvl )
                            << "Calculate: PID= "
                            << pcFSPassD->pcExPceD[ iter ]->pcPce->prod_id
                            << ", UFDD Frc_PU_Wid status="
                            << cUFDD::Image( ufdd_status )
                            << END_OF_MESSAGE;
                    }
                }
                if ( ufdd_status != cUFDD::valid )
                {
                    // set desired force to extreme value NORMALLY negative
                    force_pu_wid_buf =
                        pcFSPassD->pcPEnvD->force_pu_wid_lim[ minl ] - 10.0F;
                        if ( pcFSPassD->pcPEnvD->dprf_dfrcw < 0.0 )
                        {
                            force_pu_wid_buf =
                                pcFSPassD->pcPEnvD->force_pu_wid_lim[ maxl ] + 10.0F;
                        }
                }
                //------------------------------------------------------------------
                // Restrict the maximum rolling force per unit piece width component
                // of the envelope to within the rolling force per unit piece width
                // limits.
                //------------------------------------------------------------------
                pcFSPassD->pcPEnvD->force_pu_wid_env[ maxl ] =
                    cMathUty::Clamp( force_pu_wid_buf,
                                     pcFSPassD->pcPEnvD->force_pu_wid_lim[ minl ],
                                     pcFSPassD->pcPEnvD->force_pu_wid_lim[ maxl ] );

                //--------------------------------------------------------------
                // Indicate that the required rolling force per unit piece width
                // change was restricted.
                //--------------------------------------------------------------
                force_chg_clmp =
                    pcFSPassD->pcPEnvD->force_pu_wid_env[ maxl ] != force_pu_wid_buf;

                if ( force_chg_clmp &&
                     pcFSPassD->pcFSStdD[ iter ]->pcLRGD->pce_infl_cof >
                         pcFSPassD->pcPEnvD->pcPEnv->pce_infl_cof_mn )
                {
                    force_chg_clmp = false;

                    //--------------------------------------------------------------
                    // Attempt to change the effective entry per unit profile.  This
                    // will not help the current pass rolling force per unit piece
                    // width, but may change the previous pass rolling force per
                    // unit piece width.  Use the piece critical buckling limit for
                    // a center buckle flatness defect as a possible starting point.
                    //--------------------------------------------------------------
                    line_num = __LINE__;
                    istd_ex_pu_prf =
                        pcFSPassD->pcFSStdD[ iter ]->pcLRGD->Istd_Ex_PU_Prf0 (
                                   pcFSPassD->pcLPceD->strn_rlf_cof,
                                   pcFSPassD->pcPEnvD->std_ex_strn_lim[ cb ],
                                   ef_ex_pu_prf                               );

                    line_num = __LINE__;
                    ef_en_pu_prf =
                        pcFSPassD->pcFSStdD[ iter ]->pcLRGD->Ef_En_PU_Prf5 (
                                   pcFSPassD->pcLPceD->strn_rlf_cof,
                                   pcFSPassD->pcPEnvD->std_ex_strn_lim[ cb ],
                                   istd_ex_pu_prf                          );

                    //------------------------------------------------------------
                    // Restrict the effective entry per unit profile to within the
                    // effective per unit profile envelope.
                    //------------------------------------------------------------
                    line_num = __LINE__;
                    ef_en_pu_prf_buf =
                        cMathUty::Clamp(
                               ef_en_pu_prf,
                               pcFSPassD->pcPrvAct->pcPEnvD->ef_pu_prf_env[ minl ],
                               pcFSPassD->pcPrvAct->pcPEnvD->ef_pu_prf_env[ maxl ] );

                    //---------------------------------------------------------
                    // Indicate that a move should be made to the previous non-
                    // dummied pass if an effective per unit profile change is
                    // possible.
                    //---------------------------------------------------------
                    move_prv[ maxl ] =
                        ef_en_pu_prf_buf !=
                            pcFSPassD->pcPrvAct->pcPEnvD->ef_pu_prf_env[ maxl ] &&
                        pcFSPassD->pcPrvAct->pcPEnvD->ef_pu_prf_env[ minl ] !=
                            pcFSPassD->pcPrvAct->pcPEnvD->ef_pu_prf_env[ maxl ];

                    //------------------------------------------------------------
                    // Capture the maximum effective entry per unit profile limit.
                    //------------------------------------------------------------
                    pcFSPassD->pcPrvAct->pcPEnvD->ef_pu_prf_lim[ maxl ] =
                        ef_en_pu_prf_buf;

                    if ( !move_prv[ maxl ] )
                    {
                        ef_en_pu_prf_buf =
                            pcFSPassD->pcPrvAct->pcPEnvD->ef_pu_prf_env[ maxl ];
                    }
                }
                //----------------------------------------------------------
                // Calculate the UFD roll gap per unit profile for the given
                // conditions.
                //----------------------------------------------------------
                line_num = __LINE__;
                ufd_pu_prf =
                    pcFSPassD->pcFSStdD[ iter ]->pcLRGD->UFD_PU_Prf3(
                                     pcFSPassD->pcLPceD->strn_rlf_cof,
                                     ef_en_pu_prf_buf,
                                     ef_ex_pu_prf);

                //------------------------------------------------------------
                // Calculate the following required composite roll stack crown
                // quantities:
                //     Piece to work roll stack crown
                //     Work roll to backup roll stack crown
                //------------------------------------------------------------
                line_num = __LINE__;
                pcFSPassD->pcFSStdD[ iter ]->pcUFDD->Crns(
                          ufd_pu_prf * pcFSPassD->pcFSStdD[ iter ]->pcExPceD->thick,
                          pcFSPassD->pcPEnvD->force_pu_wid_env[ maxl ],
                          pcFSPassD->pcPEnvD->force_bnd_env[ maxl ],
                          pce_wr_crn,
                          wr_br_crn );

                //-----------------------------------------------------------
                // Calculate the maximum roll shift position component of the
                // envelope for the given conditions.
                //-----------------------------------------------------------
                line_num = __LINE__;
                pcFSPassD->pcFSStdD[ iter ]->pcCRLCD->
                    Shft_Pos( pce_wr_crn,
                              pcFSPassD->pcPEnvD->angl_pc_env[ maxl ],
                              pcFSPassD->pcFSStdD[ iter ]->wr_shft_lim,
                              pcFSPassD->pcPEnvD->pos_shft_env[ maxl ],
                              crlcd_status );

                DMSG( -diagLvl ) << "@@Min@@,pos_shft_env =  "<< pcFSPassD->pcPEnvD->pos_shft_env[ minl ] << ",std No=" <<pcFSPassD->pcFSStdD[ iter ]->stdNum << END_OF_MESSAGE;
                DMSG( -diagLvl ) << "@@Max@@,pos_shft_env =  "<< pcFSPassD->pcPEnvD->pos_shft_env[ maxl ] << ",std No=" <<pcFSPassD->pcFSStdD[ iter ]->stdNum << END_OF_MESSAGE;

                if ( crlcd_status != cCRLCD::valid )
                {
                    DMSG( diagLvl )
                        << "Calculate: PID="
                        << pcFSPassD->pcExPceD[ iter ]->pcPce->prod_id
                        << ", CRLCD Crns status="
                        << cCRLCD::Image( crlcd_status )
                        << END_OF_MESSAGE;
                }
                //------------------------------------------------------------------
                // Re-calculate the following composite roll stack crown quantities:
                //     Piece to work roll stack crown
                //     Work roll to backup roll stack crown
                //------------------------------------------------------------------
                line_num = __LINE__;
                pcFSPassD->pcFSStdD[ iter ]->pcCRLCD->
                    Crns( pcFSPassD->pcPEnvD->pos_shft_env[ maxl ],
                          pcFSPassD->pcPEnvD->angl_pc_env[ maxl ],
                          pcFSPassD->pcPEnvD->pce_wr_crn_env[ maxl ],
                          pcFSPassD->pcPEnvD->wr_br_crn_env[ maxl ] );

                DMSG( -diagLvl ) << "@@Min@@,pos_shft_env =  "<< pcFSPassD->pcPEnvD->pos_shft_env[ minl ] << ",std No=" <<pcFSPassD->pcFSStdD[ iter ]->stdNum << END_OF_MESSAGE;
                DMSG( -diagLvl ) << "@@Max@@,pos_shft_env =  "<< pcFSPassD->pcPEnvD->pos_shft_env[ maxl ] << ",std No=" <<pcFSPassD->pcFSStdD[ iter ]->stdNum << END_OF_MESSAGE;

                //--------------------------------------------------------------
                // Calculate the maximum piece to work roll stack crown envelope
                // component.
                //--------------------------------------------------------------
                line_num = __LINE__;
                pce_wr_crn = pcFSPassD->pcFSStdD[ iter ]->pcUFDD->Pce_WR_Crn(
                                ufd_pu_prf * pcFSPassD->pcFSStdD[ iter ]->pcExPceD->thick,
                                pcFSPassD->pcPEnvD->force_pu_wid_env [ maxl ],
                                pcFSPassD->pcPEnvD->force_bnd_env    [ maxl ],
                                pcFSPassD->pcPEnvD->wr_br_crn_env    [ maxl ] );

                //-----------------------------------------------------------------
                // Calculate the maximum pair cross angle component of the envelope
                // for the given conditions.
                //-----------------------------------------------------------------
                line_num = __LINE__;
                pcFSPassD->pcFSStdD[ iter ]->pcCRLCD->PC_Angl(
                             pce_wr_crn,
                             pcFSPassD->pcPEnvD->angl_pc_env[ maxl ],
                             pcFSPassD->pcFSStdD[ iter ]->angl_pc_lim );

                //------------------------------------------------------------------
                // Re-calculate the following composite roll stack crown quantities:
                //     Piece to work roll stack crown
                //     Work roll to backup roll stack crown
                //------------------------------------------------------------------
                line_num = __LINE__;
                pcFSPassD->pcFSStdD[ iter ]->pcCRLCD->Crns (
                          pcFSPassD->pcPEnvD->pos_shft_env  [ maxl ],
                          pcFSPassD->pcPEnvD->angl_pc_env   [ maxl ],
                          pcFSPassD->pcPEnvD->pce_wr_crn_env[ maxl ],
                          pcFSPassD->pcPEnvD->wr_br_crn_env [ maxl ] );

                DMSG( -diagLvl ) << "@@Min@@,pos_shft_env =  "<< pcFSPassD->pcPEnvD->pos_shft_env[ minl ] << ",std No=" <<pcFSPassD->pcFSStdD[ iter ]->stdNum << END_OF_MESSAGE;
                DMSG( -diagLvl ) << "@@Max@@,pos_shft_env =  "<< pcFSPassD->pcPEnvD->pos_shft_env[ maxl ] << ",std No=" <<pcFSPassD->pcFSStdD[ iter ]->stdNum << END_OF_MESSAGE;

                //----------------------------------------------------------
                // Calculate the maximum roll bending force component of the
                // envelope for the given conditions.
                //----------------------------------------------------------
                line_num = __LINE__;
                pcFSPassD->pcFSStdD[ iter ]->pcUFDD->Bnd_Frc(
                             ufd_pu_prf * pcFSPassD->pcFSStdD[ iter ]->pcExPceD->thick,
                             pcFSPassD->pcPEnvD->force_pu_wid_env [ maxl ],
                             pcFSPassD->pcPEnvD->pce_wr_crn_env   [ maxl ],
                             pcFSPassD->pcPEnvD->wr_br_crn_env    [ maxl ],
                             pcFSPassD->pcFSStdD[ iter ]->force_bnd_lim,
                             pcFSPassD->pcPEnvD->force_bnd_env    [ maxl ],
                             force_bnd_des );

                force_bnd_clmp =
                    force_bnd_des != pcFSPassD->pcPEnvD->force_bnd_env[ maxl ];

                //-----------------------------------------------------------------
                // Calculate the maximum UFD roll gap per unit profile component of
                // the envelope for the given conditions.
                //-----------------------------------------------------------------
                line_num = __LINE__;
                pcFSPassD->pcPEnvD->ufd_pu_prf_env[ maxl ] =
                    pcFSPassD->pcFSStdD[ iter ]->pcUFDD->Prf (
                             pcFSPassD->pcPEnvD->force_pu_wid_env[ maxl ],
                             pcFSPassD->pcPEnvD->force_bnd_env   [ maxl ],
                             pcFSPassD->pcPEnvD->pce_wr_crn_env  [ maxl ],
                             pcFSPassD->pcPEnvD->wr_br_crn_env   [ maxl ] ) /
                    pcFSPassD->pcFSStdD[ iter ]->pcExPceD->thick;

                // if the above changes were limited change the PUE entry
                if ( force_bnd_clmp &&
                     pcFSPassD->pcFSStdD[ iter ]->pcLRGD->pce_infl_cof >
                         pcFSPassD->pcPEnvD->pcPEnv->pce_infl_cof_mn )
                {
                    force_bnd_clmp = false;

                    //-------------------------------------------------------------
                    // Calculate the effective entry per unit profile for the given
                    // conditions.
                    //-------------------------------------------------------------
                    line_num = __LINE__;
                    ef_en_pu_prf =
                        pcFSPassD->pcFSStdD[ iter ]->pcLRGD->Ef_En_PU_Prf3(
                                       pcFSPassD->pcLPceD->strn_rlf_cof,
                                       pcFSPassD->pcPEnvD->ufd_pu_prf_env[ maxl ],
                                       ef_ex_pu_prf );

                    //------------------------------------------------------------
                    // Restrict the effective entry per unit profile to within the
                    // effective per unit profile envelope.
                    //------------------------------------------------------------
                    line_num = __LINE__;
                    ef_en_pu_prf_buf =
                        cMathUty::Clamp( ef_en_pu_prf,
                                         pcFSPassD->pcPrvAct->pcPEnvD->ef_pu_prf_env[ minl ],
                                         pcFSPassD->pcPrvAct->pcPEnvD->ef_pu_prf_env[ maxl ] );

                    //---------------------------------------------------------
                    // Indicate that a move should be made to the previous non-
                    // dummied pass if an effective per unit profile change is
                    // possible.
                    //---------------------------------------------------------
                    line_num = __LINE__;
                    move_prv[ maxl ] =
                        move_prv[ maxl ] ||
                        ( ef_en_pu_prf_buf != pcFSPassD->pcPrvAct->pcPEnvD->ef_pu_prf_lim[ maxl ] &&
                          pcFSPassD->pcPrvAct->pcPEnvD->ef_pu_prf_env[ minl ] !=
                              pcFSPassD->pcPrvAct->pcPEnvD->ef_pu_prf_env[ maxl ] );

                    //----------------------------------------------------
                    // Capture the maximum effective per unit crown limit.
                    //----------------------------------------------------
                    pcFSPassD->pcPrvAct->pcPEnvD->ef_pu_prf_lim[ maxl ] =
                        ef_en_pu_prf_buf;
                }
            }
            if ( !move_prv[ maxl ] )
            {
                //-----------------------------------------------------------
                // Calculate the stand exit differential strain for the given
                // conditions.
                //-----------------------------------------------------------
                line_num = __LINE__;
                std_ex_strn =
                    pcFSPassD->pcFSStdD[ iter ]->pcLRGD->Std_Ex_Strn1 (
                                 pcFSPassD->pcPrvAct->pcPEnvD->ef_pu_prf_env[ maxl ],
                                 pcFSPassD->pcPEnvD->ufd_pu_prf_env         [ maxl ] );

//@2ND(M16M062)_b begin
                //if ( std_ex_strn > pcFSPassD->pcPEnvD->std_ex_strn_lim[ we ] )
                if ( 0 > 1 )
//@2ND(M16M062)_b end
                {
                    //-----------------------------------------------------------
                    // Select a lower rolling force per unit piece width by using
                    // the piece critical buckling limit for a wavy edge flatness
                    // defect.
                    //-----------------------------------------------------------
                    line_num = __LINE__;
                    ufd_pu_prf =
                        pcFSPassD->pcFSStdD[ iter ]->pcLRGD->UFD_PU_Prf1 (
                              pcFSPassD->pcPrvAct->pcPEnvD->ef_pu_prf_env[ maxl ],
                              pcFSPassD->pcPEnvD->std_ex_strn_lim        [ we ] );

                    //---------------------------------------------------------
                    // Calculate the rolling force per unit piece for the given
                    // conditions.
                    //---------------------------------------------------------
                    line_num = __LINE__;
                    pcFSPassD->pcFSStdD[ iter ]->pcUFDD->Frc_PU_Wid (
                            ufd_pu_prf * pcFSPassD->pcFSStdD[ iter ]->pcExPceD->thick,
                            pcFSPassD->pcPEnvD->force_bnd_env  [ maxl ],
                            pcFSPassD->pcPEnvD->pce_wr_crn_env [ maxl ],
                            pcFSPassD->pcPEnvD->wr_br_crn_env  [ maxl ],
                            force_pu_wid_buf,
                            ufdd_status );

                    if ( ufdd_status != cUFDD::valid )
                    {
                        DMSG( diagLvl )
                            << "Calculate: PID="
                            << pcFSPassD->pcExPceD[ iter ]->pcPce->prod_id
                            << ", UFDD Frc_PU_Wid status="
                            << cUFDD::Image( ufdd_status )
                            << END_OF_MESSAGE;

                        // set desired force to anextreme value NORMALLY negative
                        force_pu_wid_buf =
                            pcFSPassD->pcPEnvD->force_pu_wid_lim[ minl ] - 10.0F;
                        if ( pcFSPassD->pcPEnvD->dprf_dfrcw < 0.0 )
                        {
                            force_pu_wid_buf =
                                pcFSPassD->pcPEnvD->force_pu_wid_lim[ maxl ] + 10.0F;
                        }
                    }
                    //----------------------------------------------------------
                    // Restrict the maximum rolling force per unit piece width
                    // component of the envelope to within the rolling force per
                    // unit piece width limits.
                    //----------------------------------------------------------
                    line_num = __LINE__;
                    pcFSPassD->pcPEnvD->force_pu_wid_env[ maxl ] =
                        cMathUty::Clamp( force_pu_wid_buf,
                                         pcFSPassD->pcPEnvD->force_pu_wid_lim[ minl ],
                                         pcFSPassD->pcPEnvD->force_pu_wid_lim[ maxl ] );

                    if ( pcFSPassD->pcPEnvD->force_pu_wid_env[ maxl ] != force_pu_wid_buf )
                    {
                        //------------------------------------------------------
                        // Calculate the following required composite roll stack
                        // crown quantities:
                        //     Piece to work roll stack crown
                        //     Work roll to backup roll stack crown
                        //------------------------------------------------------
                        line_num = __LINE__;
                        pcFSPassD->pcFSStdD[ iter ]->pcUFDD->Crns(
                                  ufd_pu_prf * pcFSPassD->pcFSStdD[ iter ]->pcExPceD->thick,
                                  pcFSPassD->pcPEnvD->force_pu_wid_env[ maxl ],
                                  pcFSPassD->pcPEnvD->force_bnd_env[ maxl ],
                                  pce_wr_crn,
                                  wr_br_crn );

                        //----------------------------------------------------
                        // Calculate the maximum roll shift position component
                        // of the envelope for the given conditions.
                        //----------------------------------------------------
                        line_num = __LINE__;
                        pcFSPassD->pcFSStdD[ iter ]->pcCRLCD->Shft_Pos (
                                      pce_wr_crn,
                                      pcFSPassD->pcPEnvD->angl_pc_env[ maxl ],
                                      pcFSPassD->pcFSStdD[ iter ]->wr_shft_lim,
                                      pcFSPassD->pcPEnvD->pos_shft_env[ maxl ],
                                      crlcd_status                      );

                DMSG( -diagLvl ) << "@@Min@@,pos_shft_env =  "<< pcFSPassD->pcPEnvD->pos_shft_env[ minl ] << ",std No=" <<pcFSPassD->pcFSStdD[ iter ]->stdNum << END_OF_MESSAGE;
                DMSG( -diagLvl ) << "@@Max@@,pos_shft_env =  "<< pcFSPassD->pcPEnvD->pos_shft_env[ maxl ] << ",std No=" <<pcFSPassD->pcFSStdD[ iter ]->stdNum << END_OF_MESSAGE;

                        if ( crlcd_status != cCRLCD::valid )
                        {
                            DMSG( diagLvl )
                                << "Calculate: PID="
                                << pcFSPassD->pcExPceD[ iter ]->pcPce->prod_id
                                << ", CRLCD Crns status="
                                << cCRLCD::Image( crlcd_status )
                                << END_OF_MESSAGE;
                        }
                        //------------------------------------------------------
                        // Re-calculate the following composite roll stack crown
                        // quantities:
                        //     Piece to work roll stack crown
                        //     Work roll to backup roll stack crown
                        //------------------------------------------------------
                        line_num = __LINE__;
                        pcFSPassD->pcFSStdD[ iter ]->pcCRLCD->Crns (
                                  pcFSPassD->pcPEnvD->pos_shft_env  [ maxl ],
                                  pcFSPassD->pcPEnvD->angl_pc_env   [ maxl ],
                                  pcFSPassD->pcPEnvD->pce_wr_crn_env[ maxl ],
                                  pcFSPassD->pcPEnvD->wr_br_crn_env [ maxl ] );

                DMSG( -diagLvl ) << "@@Min@@,pos_shft_env =  "<< pcFSPassD->pcPEnvD->pos_shft_env[ minl ] << ",std No=" <<pcFSPassD->pcFSStdD[ iter ]->stdNum << END_OF_MESSAGE;
                DMSG( -diagLvl ) << "@@Max@@,pos_shft_env =  "<< pcFSPassD->pcPEnvD->pos_shft_env[ maxl ] << ",std No=" <<pcFSPassD->pcFSStdD[ iter ]->stdNum << END_OF_MESSAGE;

                        //-----------------------------------------------------
                        // Calculate the maximum piece to work roll stack crown
                        // envelope component.
                        //-----------------------------------------------------
                        line_num = __LINE__;
                        pce_wr_crn =
                            pcFSPassD->pcFSStdD[ iter ]->pcUFDD->Pce_WR_Crn  (
                                 ufd_pu_prf * pcFSPassD->pcFSStdD[ iter ]->pcExPceD->thick,
                                 pcFSPassD->pcPEnvD->force_pu_wid_env[ maxl ],
                                 pcFSPassD->pcPEnvD->force_bnd_env[ maxl ],
                                 pcFSPassD->pcPEnvD->wr_br_crn_env[ maxl ] );

                        //--------------------------------------------------------
                        // Calculate the maximum pair cross angle component of the
                        // envelope for the given conditions.
                        //--------------------------------------------------------
                        line_num = __LINE__;
                        pcFSPassD->pcFSStdD[ iter ]->pcCRLCD->PC_Angl (
                                     pce_wr_crn,
                                     pcFSPassD->pcPEnvD->angl_pc_env[ maxl ],
                                     pcFSPassD->pcFSStdD[ iter ]->angl_pc_lim );

                        //------------------------------------------------------
                        // Re-calculate the following composite roll stack crown
                        // quantities:
                        //     Piece to work roll stack crown
                        //     Work roll to backup roll stack crown
                        //------------------------------------------------------
                        line_num = __LINE__;
                        pcFSPassD->pcFSStdD[ iter ]->pcCRLCD->Crns(
                                  pcFSPassD->pcPEnvD->pos_shft_env  [ maxl ],
                                  pcFSPassD->pcPEnvD->angl_pc_env   [ maxl ],
                                  pcFSPassD->pcPEnvD->pce_wr_crn_env[ maxl ],
                                  pcFSPassD->pcPEnvD->wr_br_crn_env [ maxl ] );

                DMSG( -diagLvl ) << "@@Min@@,pos_shft_env =  "<< pcFSPassD->pcPEnvD->pos_shft_env[ minl ] << ",std No=" <<pcFSPassD->pcFSStdD[ iter ]->stdNum << END_OF_MESSAGE;
                DMSG( -diagLvl ) << "@@Max@@,pos_shft_env =  "<< pcFSPassD->pcPEnvD->pos_shft_env[ maxl ] << ",std No=" <<pcFSPassD->pcFSStdD[ iter ]->stdNum << END_OF_MESSAGE;

                        //----------------------------------------------------------
                        // Calculate the maximum roll bending force component of the
                        // envelope for the given conditions.
                        //-----------------------------------------------------------
                        line_num = __LINE__;
                        pcFSPassD->pcFSStdD[ iter ]->pcUFDD->Bnd_Frc (
                              ufd_pu_prf * pcFSPassD->pcFSStdD[ iter ]->pcExPceD->thick,
                              pcFSPassD->pcPEnvD->force_pu_wid_env [ maxl ],
                              pcFSPassD->pcPEnvD->pce_wr_crn_env   [ maxl ],
                              pcFSPassD->pcPEnvD->wr_br_crn_env    [ maxl ],
                              pcFSPassD->pcFSStdD[ iter ]->force_bnd_lim,
                              pcFSPassD->pcPEnvD->force_bnd_env    [ maxl ],
                              force_bnd_des );

                        //---------------------------------------------------------
                        // Capture the current pass being evaluated as the limiting
                        // pass for the maximum component of the envelope.
                        //---------------------------------------------------------
                        if ( pas_env_lim[ maxl ] == 0 )
                        {
                            pas_env_lim[ maxl ] = pcFSPassD->pcPass->num;
                        }
                    }
                    //--------------------------------------------------------------
                    // Calculate the maximum UFD roll gap per unit profile component
                    // of the envelope for the given conditions.
                    //--------------------------------------------------------------
                    line_num = __LINE__;
                    pcFSPassD->pcPEnvD->ufd_pu_prf_env[ maxl ] =
                        pcFSPassD->pcFSStdD[ iter ]->pcUFDD->Prf (
                                 pcFSPassD->pcPEnvD->force_pu_wid_env[ maxl ],
                                 pcFSPassD->pcPEnvD->force_bnd_env   [ maxl ],
                                 pcFSPassD->pcPEnvD->pce_wr_crn_env  [ maxl ],
                                 pcFSPassD->pcPEnvD->wr_br_crn_env   [ maxl ] ) /
                        pcFSPassD->pcFSStdD[ iter ]->pcExPceD->thick;
                }
 //@2ND(M16M062)_b begin
                //if ( std_ex_strn < pcFSPassD->pcPEnvD->std_ex_strn_lim[ cb ] &&
                if ( 1 < 0 &&
 //@2ND(M16M062)_b begin
                     pcFSPassD->pcFSStdD[ iter ]->pcLRGD->pce_infl_cof >
                         pcFSPassD->pcPEnvD->pcPEnv->pce_infl_cof_mn )
                {
                    //-------------------------------------------------------------
                    // Select a lower composite roll stack crown by using the piece
                    // critical buckling limit for a center buckle flatness defect.
                    //-------------------------------------------------------------
                    line_num = __LINE__;
                    ufd_pu_prf =
                        pcFSPassD->pcFSStdD[ iter ]->pcLRGD->UFD_PU_Prf1 (
                               pcFSPassD->pcPrvAct->pcPEnvD->ef_pu_prf_env[ maxl ],
                               pcFSPassD->pcPEnvD->std_ex_strn_lim [ cb ] );

                    //------------------------------------------------------------
                    // Calculate the following required composite roll stack crown
                    // quantities:
                    //     Piece to work roll stack crown
                    //     Work roll to backup roll stack crown
                    //------------------------------------------------------------
                    line_num = __LINE__;
                    pcFSPassD->pcFSStdD[ iter ]->pcUFDD->Crns (
                              ufd_pu_prf * pcFSPassD->pcFSStdD[ iter ]->pcExPceD->thick,
                              pcFSPassD->pcPEnvD->force_pu_wid_env[ maxl ],
                              pcFSPassD->pcPEnvD->force_bnd_env[ maxl ],
                              pce_wr_crn,
                              wr_br_crn );

                    //-----------------------------------------------------------
                    // Calculate the maximum roll shift position component of the
                    // envelope for the given conditions.
                    //-----------------------------------------------------------
                    line_num = __LINE__;
                    pcFSPassD->pcFSStdD[ iter ]->pcCRLCD->Shft_Pos (
                                  pce_wr_crn,
                                  pcFSPassD->pcPEnvD->angl_pc_env[ maxl ],
                                  pcFSPassD->pcFSStdD[ iter ]->wr_shft_lim,
                                  pcFSPassD->pcPEnvD->pos_shft_env[ maxl ],
                                  crlcd_status );

                DMSG( -diagLvl ) << "@@Min@@,pos_shft_env =  "<< pcFSPassD->pcPEnvD->pos_shft_env[ minl ] << ",std No=" <<pcFSPassD->pcFSStdD[ iter ]->stdNum << END_OF_MESSAGE;
                DMSG( -diagLvl ) << "@@Max@@,pos_shft_env =  "<< pcFSPassD->pcPEnvD->pos_shft_env[ maxl ] << ",std No=" <<pcFSPassD->pcFSStdD[ iter ]->stdNum << END_OF_MESSAGE;

                    if ( crlcd_status != cCRLCD::valid )
                    {
                        DMSG( diagLvl )
                            << "Calculate:PID="
                            << pcFSPassD->pcExPceD[ iter ]->pcPce->prod_id
                            << ", CRLCD Crns status="
                            << cCRLCD::Image( crlcd_status )
                            << END_OF_MESSAGE;
                    }
                    //------------------------------------------------------
                    // Re-calculate the following composite roll stack crown
                    // quantities:
                    //     Piece to work roll stack crown
                    //     Work roll to backup roll stack crown
                    //------------------------------------------------------
                    line_num = __LINE__;
                    pcFSPassD->pcFSStdD[ iter ]->pcCRLCD->Crns(
                              pcFSPassD->pcPEnvD->pos_shft_env  [ maxl ],
                              pcFSPassD->pcPEnvD->angl_pc_env   [ maxl ],
                              pcFSPassD->pcPEnvD->pce_wr_crn_env[ maxl ],
                              pcFSPassD->pcPEnvD->wr_br_crn_env [ maxl ] );

                DMSG( -diagLvl ) << "@@Min@@,pos_shft_env =  "<< pcFSPassD->pcPEnvD->pos_shft_env[ minl ] << ",std No=" <<pcFSPassD->pcFSStdD[ iter ]->stdNum << END_OF_MESSAGE;
                DMSG( -diagLvl ) << "@@Max@@,pos_shft_env =  "<< pcFSPassD->pcPEnvD->pos_shft_env[ maxl ] << ",std No=" <<pcFSPassD->pcFSStdD[ iter ]->stdNum << END_OF_MESSAGE;

                    //--------------------------------------------------------------
                    // Calculate the maximum piece to work roll stack crown envelope
                    // component.
                    //--------------------------------------------------------------
                    line_num = __LINE__;
                    pce_wr_crn =
                        pcFSPassD->pcFSStdD[ iter ]->pcUFDD->Pce_WR_Crn(
                             ufd_pu_prf * pcFSPassD->pcFSStdD[ iter ]->pcExPceD->thick,
                             pcFSPassD->pcPEnvD->force_pu_wid_env [ maxl ],
                             pcFSPassD->pcPEnvD->force_bnd_env    [ maxl ],
                             pcFSPassD->pcPEnvD->wr_br_crn_env    [ maxl ] );

                    //--------------------------------------------------------
                    // Calculate the maximum pair cross angle component of the
                    // envelope for the given conditions.
                    //--------------------------------------------------------
                    line_num = __LINE__;
                    pcFSPassD->pcFSStdD[ iter ]->pcCRLCD->PC_Angl (
                                 pce_wr_crn,
                                 pcFSPassD->pcPEnvD->angl_pc_env[ maxl ],
                                 pcFSPassD->pcFSStdD[ iter ]->angl_pc_lim  );

                    //------------------------------------------------------
                    // Re-calculate the following composite roll stack crown
                    // quantities:
                    //     Piece to work roll stack crown
                    //     Work roll to backup roll stack crown
                    //------------------------------------------------------
                    line_num = __LINE__;
                    pcFSPassD->pcFSStdD[ iter ]->pcCRLCD->Crns(
                              pcFSPassD->pcPEnvD->pos_shft_env  [ maxl ],
                              pcFSPassD->pcPEnvD->angl_pc_env   [ maxl ],
                              pcFSPassD->pcPEnvD->pce_wr_crn_env[ maxl ],
                              pcFSPassD->pcPEnvD->wr_br_crn_env [ maxl ] );

                DMSG( -diagLvl ) << "@@Min@@,pos_shft_env =  "<< pcFSPassD->pcPEnvD->pos_shft_env[ minl ] << ",std No=" <<pcFSPassD->pcFSStdD[ iter ]->stdNum << END_OF_MESSAGE;
                DMSG( -diagLvl ) << "@@Max@@,pos_shft_env =  "<< pcFSPassD->pcPEnvD->pos_shft_env[ maxl ] << ",std No=" <<pcFSPassD->pcFSStdD[ iter ]->stdNum << END_OF_MESSAGE;

                    //----------------------------------------------------------
                    // Calculate the maximum roll bending force component of the
                    // envelope for the given conditions.
                    //----------------------------------------------------------
                    line_num = __LINE__;
                    pcFSPassD->pcFSStdD[ iter ]->pcUFDD->Bnd_Frc (
                          ufd_pu_prf * pcFSPassD->pcFSStdD[ iter ]->pcExPceD->thick,
                          pcFSPassD->pcPEnvD->force_pu_wid_env [ maxl ],
                          pcFSPassD->pcPEnvD->pce_wr_crn_env   [ maxl ],
                          pcFSPassD->pcPEnvD->wr_br_crn_env    [ maxl ],
                          pcFSPassD->pcFSStdD[ iter ]->force_bnd_lim,
                          pcFSPassD->pcPEnvD->force_bnd_env    [ maxl ],
                          force_bnd_des );

                    force_bnd_clmp =
                        force_bnd_des != pcFSPassD->pcPEnvD->force_bnd_env[ maxl ];

                    if ( force_bnd_clmp )
                    {
                        force_bnd_clmp = false;

                        //----------------------------------------------------
                        // Select a higher rolling force per unit piece width.
                        //----------------------------------------------------
                        line_num = __LINE__;
                        pcFSPassD->pcFSStdD[ iter ]->pcUFDD->Frc_PU_Wid (
                                        ufd_pu_prf * pcFSPassD->pcFSStdD[ iter ]->pcExPceD->thick,
                                        pcFSPassD->pcPEnvD->force_bnd_env  [ maxl ],
                                        pcFSPassD->pcPEnvD->pce_wr_crn_env [ maxl ],
                                        pcFSPassD->pcPEnvD->wr_br_crn_env  [ maxl ],
                                        force_pu_wid_buf,
                                        ufdd_status );

                        if ( ufdd_status != cUFDD::valid )
                        {
                            DMSG( diagLvl )
                                << "Calculate: PID="
                                << pcFSPassD->pcExPceD[ iter ]->pcPce->prod_id
                                << ", UFDD Frc_PU_Wid status="
                                << cUFDD::Image( ufdd_status )
                                << END_OF_MESSAGE;

                            // set desired force to anextreme value NORMALLY negative
                            force_pu_wid_buf =
                                pcFSPassD->pcPEnvD->force_pu_wid_lim[ minl ] - 10.0F;
                            if ( pcFSPassD->pcPEnvD->dprf_dfrcw < 0.0 )
                            {
                                force_pu_wid_buf =
                                  pcFSPassD->pcPEnvD->force_pu_wid_lim[ maxl ] + 10.0F;
                            }
                        }
                        //----------------------------------------------------------
                        // Restrict the maximum rolling force per unit piece width
                        // component of the envelope to within the rolling force per
                        // unit piece width limits.
                        //----------------------------------------------------------
                        line_num = __LINE__;
                        pcFSPassD->pcPEnvD->force_pu_wid_env[ maxl ] =
                            cMathUty::Clamp( force_pu_wid_buf,
                                             pcFSPassD->pcPEnvD->force_pu_wid_lim [ minl ],
                                             pcFSPassD->pcPEnvD->force_pu_wid_lim [ maxl ] );

                        //--------------------------------------------------------
                        // Indicate that the required rolling force per unit piece
                        // width change was restricted.
                        //--------------------------------------------------------
                        force_chg_clmp =
                            pcFSPassD->pcPEnvD->force_pu_wid_env[ maxl ] != force_pu_wid_buf;
                    }
                    //--------------------------------------------------------------
                    // Calculate the maximum UFD roll gap per unit profile component
                    // of the envelope for the given conditions.
                    //--------------------------------------------------------------
                    line_num = __LINE__;
                    pcFSPassD->pcPEnvD->ufd_pu_prf_env[ maxl ] =
                        pcFSPassD->pcFSStdD[ iter ]->pcUFDD->Prf(
                                 pcFSPassD->pcPEnvD->force_pu_wid_env [ maxl ],
                                 pcFSPassD->pcPEnvD->force_bnd_env    [ maxl ],
                                 pcFSPassD->pcPEnvD->pce_wr_crn_env   [ maxl ],
                                 pcFSPassD->pcPEnvD->wr_br_crn_env    [ maxl ] ) /
                        pcFSPassD->pcFSStdD[ iter ]->pcExPceD->thick;

                    if ( force_chg_clmp )
                    {
                        force_chg_clmp = false;

                        //-------------------------------------------------------
                        // Attempt to change the effective entry per unit profile
                        // This will not help the current pass rolling force per
                        // unit piece width, but may change the previous pass
                        // rolling force per unit piece width.  Use the piece
                        // critical buckling limit for a center buckle flatness
                        // defect as a possible starting point.
                        //-------------------------------------------------------
                        line_num = __LINE__;
                        ef_en_pu_prf =
                            pcFSPassD->pcFSStdD[ iter ]->pcLRGD->Ef_En_PU_Prf1 (
                                  pcFSPassD->pcPEnvD->ufd_pu_prf_env[ maxl ],
                                  pcFSPassD->pcPEnvD->std_ex_strn_lim[ cb ]    );

                        //--------------------------------------------------------
                        // Restrict the effective entry per unit profile to within
                        // the effective per unit profile envelope.
                        //--------------------------------------------------------
                        line_num = __LINE__;
                        ef_en_pu_prf_buf =
                            cMathUty::Clamp( ef_en_pu_prf,
                                             pcFSPassD->pcPrvAct->pcPEnvD->ef_pu_prf_env[ minl ],
                                             pcFSPassD->pcPrvAct->pcPEnvD->ef_pu_prf_env[ maxl ] );

                        //---------------------------------------------------------
                        // Indicate that a move should be made to the previous non-
                        // dummied pass if an effective per unit profile change is
                        // possible.
                        //---------------------------------------------------------
                        move_prv[ maxl ] =
                            ef_en_pu_prf !=
                                pcFSPassD->pcPrvAct->pcPEnvD->ef_pu_prf_env[ maxl ] &&
                                ( pcFSPassD->pcPrvAct->pcPEnvD->ef_pu_prf_env[ minl ] !=
                                  pcFSPassD->pcPrvAct->pcPEnvD->ef_pu_prf_env[ maxl ] );

                        pcFSPassD->pcPrvAct->pcPEnvD->ef_pu_prf_lim[ maxl ] = ef_en_pu_prf;
                    }
                }
            }
            //------------------------------------------------------------------
            // Calculate the maximum effective per unit profile component of the
            // envelope for the given conditions.
            //------------------------------------------------------------------
            line_num = __LINE__;

            DMSG( -diagLvl ) << "@@maxl@@,ef_pu_prf_env =  "<< pcFSPassD->pcPEnvD->ef_pu_prf_env[ maxl ] << ",std No=" <<pcFSPassD->pcFSStdD[ iter ]->stdNum << END_OF_MESSAGE;

            pcFSPassD->pcPEnvD->ef_pu_prf_env[ maxl ] =
                pcFSPassD->pcFSStdD[ iter ]->pcLRGD->Ef_Ex_PU_Prf3 (
                        pcFSPassD->pcLPceD->strn_rlf_cof,
                        pcFSPassD->pcPrvAct->pcPEnvD->ef_pu_prf_env[ maxl ],
                        pcFSPassD->pcPEnvD->ufd_pu_prf_env         [ maxl ] );

            DMSG( -diagLvl ) << "@@maxl@@,ef_pu_prf_env =  "<< pcFSPassD->pcPEnvD->ef_pu_prf_env[ maxl ] << ",std No=" <<pcFSPassD->pcFSStdD[ iter ]->stdNum << END_OF_MESSAGE;

            if ( move_prv[ minl ] || move_prv[ maxl ] )
            {
                loop_count = loop_count + 1;

                if ( loop_count > (float)pow ((float)pcLstActFSPassD->pcPass->num - 1, 2 ) )
                {
                    if ( pcFSPassD == pcLstActFSPassD )
                    {
                        break;
                    }
                    else
                    {   //----------------------------------------------
                        // Increment pointer to the dynamic PASS object.
                        //----------------------------------------------
                        pcFSPassD = pcFSPassD->pcNxtAct;
                    }
                }
                else
                {   //----------------------------------------------
                    // Decrement pointer to the dynamic PASS object.
                    //----------------------------------------------
                    pcFSPassD = pcFSPassD->pcPrvAct;
                }
            }
            else
            {
                if ( pcFSPassD == pcLstActFSPassD )
                {   // done with all passes
                    break;
                }
                else
                {   //----------------------------------------------
                    // Increment pointer to the dynamic PASS object.
                    //----------------------------------------------
                    pcFSPassD = pcFSPassD->pcNxtAct;
                }
            }
        }
//DMSG(-diagLvl) << "Deng gsm test: PEnvD::Calculate !" << END_OF_MESSAGE;
        if ( loop_count > (float)pow( (float)(pcLstActFSPassD->pcPass->num - 2), 2 ) )
        {
            DMSG( diagLvl )
                << "Calculate: PID="
                << pcFSPassD->pcExPceD[ iter ]->pcPce->prod_id
                << ", loop counter exceeded limit="
                << loop_count
                << END_OF_MESSAGE;
        }

        //--------------------------------------------------------
        //********************************************************
        // PART 2 BALANCE FORCE CHANGES TO ACHIEVE FIXE MILL DRAFT
        //--------------------------------------------------------
        line_num = __LINE__;
        if ( redrft_perm )
        {
//DMSG(-diagLvl) << "Deng gsm test: PEnvD::Calculate redrft_perm !" << END_OF_MESSAGE;

            //-------------------------------------------------------------------
            // Determine if the total mill draft has been changed by accumulating
            // the rolling force changes, reflected to the delivery pass rolling
            // force change, at each pass.
            //-------------------------------------------------------------------

            pcLstFSPassD->pcPEnvD->force_ratio = 1.0;
            pcFSPassD = pcLstFSPassD;
            while ( pcFSPassD != NULL )
            {
                // initialize if not the last pass
                if ( pcFSPassD != pcLstFSPassD )
                {
                    //------------------------------------
                    // Initialize the rolling force ratio.
                    //------------------------------------
                    pcFSPassD->pcPEnvD->force_ratio =
                        ( ( cFSPassD* )( pcFSPassD->next_obj) )->pcPEnvD->force_ratio;
                }
                if ( !pcFSPassD->pcFSStdD[ iter ]->dummied )
                {
                    if ( pcFSPassD->pcPass->num < pcLstActFSPassD->pcPass->num )
                    {
                        //--------------------------------
                        // Update the rolling force ratio.
                        //--------------------------------
                        line_num = __LINE__;
                        pcFSPassD->pcPEnvD->force_ratio =
                            - pcFSPassD->pcPEnvD->force_ratio *
                            pcFSPassD->pcNxtAct->pcFSStdD[ iter ]->pcRollbite->DForce_DEnthick() /
                            pcFSPassD->pcFSStdD[ iter ]->pcRollbite->DForce_DExthick();
                    }
                    // determine if this is an arbitrary force pass (next pass I = 0)
                    if ( (pcFSPassD->pcPass->num != pcLstActFSPassD->pcPass->num) &&
                         (pcFSPassD->pcNxtAct->pcFSStdD[ iter ]->pcLRGD->pce_infl_cof <
                             pcFSPassD->pcPEnvD->pcPEnv->pce_infl_cof_mn) )
                    {
                        //-----------------------------------
                        // The rolling force is arbitrary and
                        // has no effect on profile.
                        //-----------------------------------
                        line_num = __LINE__;
                        force_arb =
                            force_arb + pcFSPassD->pcPEnvD->force_ratio *
                            pcFSPassD->pcFSPass->force_pert *
                            pcFSPassD->pcPEnvD->force_pu_wid;
                    }
                    else
                    {
                        line_num = __LINE__;
                        for ( i = minl; i <= maxl; i++ )
                        {
                            //----------------------------------------------------
                            // Accumulate the rolling force per unit piece width
                            // changes of the relevant passes as the delivery pass
                            // rolling force per unit piece width.
                            //----------------------------------------------------
                            force_del[ i ] =
                                force_del[ i ] +
                                pcFSPassD->pcPEnvD->force_ratio *
                                ( pcFSPassD->pcPEnvD->force_pu_wid_env[ i ] -
                                pcFSPassD->pcPEnvD->force_pu_wid );
                        }
                        line_num = __LINE__;
                        rhdel_sum =
                            rhdel_sum + pcFSPassD->pcFSStdD[ iter ]->pcExPceD->thick *
                            pcFSPassD->pcPEnvD->force_ratio /
                            pcFSPassD->pcPEnvD->dprf_dfrcw;
                    }
                }   // end if pass dummied
                if ( pcFSPassD == pcFstFSPassD )
                {
                    break;
                }
                else
                {
                    //----------------------------------------------
                    // Increment pointer to the dynamic PASS object.
                    //----------------------------------------------
                    pcFSPassD = ( cFSPassD* )( pcFSPassD->previous_obj );
                }
            }
            for ( i = minl; i <= maxl; i++ )
            {
                //------------------------------------------------------------------
                // Determine the arbitrary rolling force per unit piece width to use
                // and the change in rolling force per unit piece width * exit piece
                // thickness / alpha.
                //------------------------------------------------------------------
                line_num = __LINE__;
                if ( force_arb > fabs( force_del[ i ] ) )
                {
                    force_pu_arb[ i ] = - force_del[ i ] / force_arb;
                    force_excess[ i ] = 0.0;
                }
                else
                {
                    force_pu_arb[ i ] = - cMathUty::Sign( force_del[ i ] );
                    force_excess[ i ] =
                        - ( force_del[ i ] + force_pu_arb[ i ] * force_arb ) /
                        rhdel_sum;
                }
            }
            pcFSPassD = pcFstFSPassD;
            while ( pcFSPassD != NULL )
            {
                if ( !pcFSPassD->pcFSStdD[ iter ]->dummied )
                {   // is this not an arbitrary force pass
                    if ( ( pcFSPassD->pcPass->num < pcLstActFSPassD->pcPass->num &&
                           !( pcFSPassD->pcNxtAct->pcFSStdD[ iter ]->pcLRGD->pce_infl_cof <
                                  pcFSPassD->pcPEnvD->pcPEnv->pce_infl_cof_mn ) ) ||
                         pcFSPassD == pcLstActFSPassD )
                    {
                        for ( i = minl; i <= maxl; i++ )
                        {
                            line_num = __LINE__;
                            if ( force_excess[ i ] /
                                 pcFSPassD->pcPEnvD->dprf_dfrcw > 0.0 )
                            {
                                pcFSPassD->pcPEnvD->pu_prf_marg[ i ] =
                                    ( pcFSPassD->pcPEnvD->force_pu_wid_lim[ maxl ] -
                                    pcFSPassD->pcPEnvD->force_pu_wid_env[ i ] ) *
                                    pcFSPassD->pcPEnvD->dprf_dfrcw /
                                    pcFSPassD->pcFSStdD[ iter ]->pcExPceD->thick;
                            }
                            else
                            {
                                pcFSPassD->pcPEnvD->pu_prf_marg[ i ] =
                                    ( pcFSPassD->pcPEnvD->force_pu_wid_lim[ minl ] -
                                    pcFSPassD->pcPEnvD->force_pu_wid_env[ i ] ) *
                                    pcFSPassD->pcPEnvD->dprf_dfrcw /
                                    pcFSPassD->pcFSStdD[ iter ]->pcExPceD->thick;
                            }
                        }
                    }
                }
                if ( pcFSPassD == pcLstFSPassD )
                {
                    break;
                }
                else
                {
                    //----------------------------------------------
                    // Increment pointer to the dynamic PASS object.
                    //----------------------------------------------
                    pcFSPassD = ( cFSPassD* )( pcFSPassD->next_obj );
                }
            }
            // now we have the needed data to adjust pu profile and forces
            pcFSPassD = pcFstFSPassD;
            while ( pcFSPassD != NULL )
            {
                if ( !pcFSPassD->pcFSStdD[ iter ]->dummied )
                {   // if this is an arbitrary force stand
                    if ( pcFSPassD->pcPass->num < pcLstActFSPassD->pcPass->num &&
                         pcFSPassD->pcNxtAct->pcFSStdD[ iter ]->pcLRGD->pce_infl_cof <
                             pcFSPassD->pcNxtAct->pcPEnvD->pcPEnv->pce_infl_cof_mn )
                    {
                        //--------------------------------------------------------
                        // Set the rolling force per unit piece width on arbitrary
                        // passes.
                        //--------------------------------------------------------
                        line_num = __LINE__;
                        pcFSPassD->pcPEnvD->force_pu_wid_env[ minl ] =
                            ( 1.0F + force_pu_arb [ minl ] *
                              pcFSPassD->pcFSPass->force_pert ) *
                            pcFSPassD->pcPEnvD->force_pu_wid;
                        pcFSPassD->pcPEnvD->force_pu_wid_env[ maxl ] =
                            ( 1.0F + force_pu_arb [ maxl ] *
                              pcFSPassD->pcFSPass->force_pert ) *
                            pcFSPassD->pcPEnvD->force_pu_wid;
                    }
                    else
                    {
                        line_num = __LINE__;
                        scratch =
                            pcFSPassD->pcFSStdD[ iter ]->pcExPceD->thick /
                            pcFSPassD->pcPEnvD->dprf_dfrcw;

                        for ( i = minl; i <= maxl; i++ )
                        {
                            ef_pu_prf_chg = force_excess[ i ];

                            if ( fabs( ef_pu_prf_chg ) >
                                     fabs( pcFSPassD->pcPEnvD->pu_prf_marg[ i ] ) )
                            {
                                ef_pu_prf_chg =
                                    pcFSPassD->pcPEnvD->pu_prf_marg[ i ];
                            }
                            //-------------------------------------------------
                            // Modify the rolling force per unit piece width to
                            // reflect the effective per unit profile change.
                            //-------------------------------------------------
                            pcFSPassD->pcPEnvD->force_pu_wid_env[ i ] =
                                pcFSPassD->pcPEnvD->force_pu_wid_env[ i ] +
                                scratch * ef_pu_prf_chg;
                        }
                    }
                }
                if ( pcFSPassD == pcLstFSPassD )
                {
                    break;
                }
                else
                {
                    //----------------------------------------------
                    // Increment pointer to the dynamic PASS object.
                    //----------------------------------------------
                    pcFSPassD = ( cFSPassD* )pcFSPassD->next_obj;
                }
            }
            //--------------------------------------------------------
            // Accumulate the rolling force changes of relevant passes
            // as the delivery pass rolling force.
            //--------------------------------------------------------
            pcFSPassD = pcFstFSPassD;
            while ( pcFSPassD != NULL )
            {
                if ( !pcFSPassD->pcFSStdD[ iter ]->dummied )
                {
                    for ( i = minl; i <= maxl; i++ )
                    {
                        line_num = __LINE__;
                        force_resid[ i ] =
                            force_resid[ i ] +
                            pcFSPassD->pcPEnvD->force_ratio *
                            ( pcFSPassD->pcPEnvD->force_pu_wid_env[ i ] -
                              pcFSPassD->pcPEnvD->force_pu_wid );
                    }
                }
                if ( pcFSPassD == pcLstFSPassD )
                {
                    break;
                }
                else
                {
                    //----------------------------------------------
                    // Increment pointer to the dynamic PASS object.
                    //----------------------------------------------
                    pcFSPassD = ( cFSPassD* )( pcFSPassD->next_obj );
                }
            }
            //--------------------------------------------------------
            // Determine the available force change margins at each
            // pass that will help correct teh envelope
            //--------------------------------------------------------
            pcFSPassD = pcFstFSPassD;
            while ( pcFSPassD != NULL )
            {
                if ( !pcFSPassD->pcFSStdD[ iter ]->dummied )
                {
                    for ( i = minl; i <= maxl; i++ )
                    {   // if residual is positive need to decrease force
                        line_num = __LINE__;
                        if ( force_resid[ i ] > 0.0 )
                        {
                            pcFSPassD->pcPEnvD->force_marg_avl[ i ] =
                                ( pcFSPassD->pcPEnvD->force_pu_wid_lim[ minl ] -
                                pcFSPassD->pcPEnvD->force_pu_wid_env[ i ] );
                        }
                        else
                        {
                            pcFSPassD->pcPEnvD->force_marg_avl[ i ] =
                                ( pcFSPassD->pcPEnvD->force_pu_wid_lim[ maxl ] -
                                pcFSPassD->pcPEnvD->force_pu_wid_env[ i ] );
                        }
                        force_marg_rem[ i ] =
                            force_marg_rem[ i ] +
                            pcFSPassD->pcPEnvD->force_marg_avl[ i ] *
                            pcFSPassD->pcPEnvD->force_ratio;
                    }
                }
                if ( pcFSPassD == pcLstFSPassD )
                {
                    break;
                }
                else
                {
                    //----------------------------------------------
                    // Increment pointer to the dynamic PASS object.
                    //----------------------------------------------
                    pcFSPassD = ( cFSPassD* )( pcFSPassD->next_obj );
                }
            }
            // adjust the margins if we could not do the fixed pu profile change
            for ( i = minl; i <= maxl; i++ )
            {
                line_num = __LINE__;
                if ( force_marg_rem[ i ] != 0.0 )
                {
                    pu_marg[ i ] = - force_resid[ i ] / force_marg_rem[ i ];
                }
            }
            pcFSPassD = pcFstFSPassD;
            while ( pcFSPassD != NULL )
            {
                if ( !pcFSPassD->pcFSStdD[ iter ]->dummied )
                {
                    line_num = __LINE__;
                    for ( i = minl; i <= maxl; i++ )
                    {
                        pcFSPassD->pcPEnvD->force_pu_wid_env[ i ] =
                            pcFSPassD->pcPEnvD->force_pu_wid_env[ i ] +
                            pu_marg[ i ] * pcFSPassD->pcPEnvD->force_marg_avl[ i ];
                        //  do we need to limit check these forces????
                    }
                }
                if ( pcFSPassD == pcLstFSPassD )
                {
                    break;
                }
                else
                {
                    //----------------------------------------------
                    // Increment pointer to the dynamic PASS object.
                    //----------------------------------------------
                    pcFSPassD = ( cFSPassD* )( pcFSPassD->next_obj );
                }
            }
        }
        line_num = __LINE__;

//DMSG(-diagLvl) << "Deng gsm test: PEnvD::Calculate after redrft_perm !" << END_OF_MESSAGE;

        pcFSPassD = pcFstFSPassD;
        while ( pcFSPassD != NULL )
        {
            if ( pcFSPassD->pcFSStdD[ iter ]->dummied )
            {
                for ( i = minl; i <= maxl; i++ )
                {
                    pcFSPassD->pcPEnvD->ef_pu_prf_env[ i ] =
                        ( ( cFSPassD* )(pcFSPassD->previous_obj) )->pcPEnvD->ef_pu_prf_env[ i ];
                }
            }
            else
            {
                for ( i = minl; i <= maxl; i++ )
                {
                    //-------------------------------------------------------------
                    // Create the minimum and maximum UFD roll gap per unit profile
                    // envelope for the given conditions.
                    //-------------------------------------------------------------
                    line_num = __LINE__;
                    pcFSPassD->pcPEnvD->ufd_pu_prf_env[ i ] =
                        pcFSPassD->pcFSStdD[ iter ]->pcUFDD->Prf (
                                 pcFSPassD->pcPEnvD->force_pu_wid_env[ i ],
                                 pcFSPassD->pcPEnvD->force_bnd_env   [ i ],
                                 pcFSPassD->pcPEnvD->pce_wr_crn_env  [ i ],
                                 pcFSPassD->pcPEnvD->wr_br_crn_env   [ i ] ) /
                        pcFSPassD->pcFSStdD[ iter ]->pcExPceD->thick;

                    //----------------------------------------------------------
                    // Create the minimum and maximum effective per unit profile
                    // envelope for the given conditions.
                    //----------------------------------------------------------
                    line_num = __LINE__;
                    pcFSPassD->pcPEnvD->ef_pu_prf_env[ i ] =
                        pcFSPassD->pcFSStdD[ iter ]->pcLRGD->Ef_Ex_PU_Prf3 (
                                   pcFSPassD->pcLPceD->strn_rlf_cof,
                                   pcFSPassD->pcPrvAct->pcPEnvD->ef_pu_prf_env[ i ],
                                   pcFSPassD->pcPEnvD->ufd_pu_prf_env[ i ] );

                    //-------------------------------------------------------------------
                    // Calculate the stand exit differential strain for the given
                    // conditions.
                    //-------------------------------------------------------------------
                    line_num = __LINE__;
                    std_ex_strn =
                        pcFSPassD->pcFSStdD[ iter ]->pcLRGD->Std_Ex_Strn1(
                                   pcFSPassD->pcPEnvD->ef_pu_prf_env[ i ],
                                   pcFSPassD->pcPEnvD->ufd_pu_prf_env[ i ] );

                    //-------------------------------------------------------------
                    // Create the minimum and maximum per unit profile envelope for
                    // the given conditions.
                    //-------------------------------------------------------------
                    line_num = __LINE__;
                    pcFSPassD->pcPEnvD->pu_prf_env[ i ] =
                        pcFSPassD->pcFSStdD[ iter ]->pcLRGD->Istd_Ex_PU_Prf0 (
                                pcFSPassD->pcLPceD->strn_rlf_cof,
                                std_ex_strn,
                                pcFSPassD->pcPEnvD->ef_pu_prf_env[ i ]       );
                }
            }
            //----------------------------------------------------------------
            // Ensure that each component comprising the coordinated envelopes
            // correctly reflects minimum and maximum.
            //----------------------------------------------------------------
            line_num = __LINE__;
            scratch =
                cMathUty::Max( pcFSPassD->pcPEnvD->pu_prf_env[ minl ],
                               pcFSPassD->pcPEnvD->pu_prf_env[ maxl ] );

            pcFSPassD->pcPEnvD->pu_prf_env[ minl ] =
                cMathUty::Min( pcFSPassD->pcPEnvD->pu_prf_env[ minl ],
                               pcFSPassD->pcPEnvD->pu_prf_env[ maxl ] );

            pcFSPassD->pcPEnvD->pu_prf_env[ maxl ] = scratch;

            scratch =
                cMathUty::Max( pcFSPassD->pcPEnvD->ef_pu_prf_env[ minl ],
                               pcFSPassD->pcPEnvD->ef_pu_prf_env[ maxl ] );

            pcFSPassD->pcPEnvD->ef_pu_prf_env[ minl ] =
                cMathUty::Min( pcFSPassD->pcPEnvD->ef_pu_prf_env[ minl ],
                               pcFSPassD->pcPEnvD->ef_pu_prf_env[ maxl ] );

            pcFSPassD->pcPEnvD->ef_pu_prf_env[ maxl ] = scratch;

            scratch =
                cMathUty::Max( pcFSPassD->pcPEnvD->ufd_pu_prf_env[ minl ],
                               pcFSPassD->pcPEnvD->ufd_pu_prf_env[ maxl ]);

            pcFSPassD->pcPEnvD->ufd_pu_prf_env[ minl ] =
                cMathUty::Min( pcFSPassD->pcPEnvD->ufd_pu_prf_env[ minl ],
                               pcFSPassD->pcPEnvD->ufd_pu_prf_env[ maxl ] );

            pcFSPassD->pcPEnvD->ufd_pu_prf_env[ maxl ] = scratch;

            scratch =
                cMathUty::Max( pcFSPassD->pcPEnvD->force_pu_wid_env[ minl ],
                               pcFSPassD->pcPEnvD->force_pu_wid_env[ maxl ] );

            pcFSPassD->pcPEnvD->force_pu_wid_env[ minl ] =
                cMathUty::Min( pcFSPassD->pcPEnvD->force_pu_wid_env[ minl ],
                               pcFSPassD->pcPEnvD->force_pu_wid_env[ maxl ] );

            pcFSPassD->pcPEnvD->force_pu_wid_env[ maxl ] = scratch;

            if ( pcFSPassD == pcLstFSPassD )
            {
                break;
            }
            else
            {
                //----------------------------------------------
                // Increment pointer to the dynamic PASS object.
                //----------------------------------------------
                pcFSPassD = ( cFSPassD* )pcFSPassD->next_obj;
            }
        }
//DMSG(-diagLvl) << "Deng gsm test: PEnvD::Calculate !" << END_OF_MESSAGE;

    } // end of try block
    catch (...)
    {
        DMSG(-diagLvl) << "Exception in pcEnvD::Calculate function "
                       << " line num " << line_num
                       << END_OF_MESSAGE;
        throw;
        return;
    }

    return;
}   // End of pcPEnvD::Calculate function


//@2ND(M16M062) end