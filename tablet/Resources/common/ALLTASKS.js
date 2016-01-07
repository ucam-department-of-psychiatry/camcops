// ALLTASKS.js

/*
    Copyright (C) 2012-2016 Rudolf Cardinal (rudolf@pobox.com).
    Department of Psychiatry, University of Cambridge.
    Funded by the Wellcome Trust.

    This file is part of CamCOPS.

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
*/

/*jslint node: true, newcap: true */
/*global L */

exports.TASKLIST = {

    // Looks best to have these in alphabetical order.

    ACE3: {
        task: 'task/Ace3',
        title: L('b_ace3'),
        tables: ['ace3'],
        maintitle: L('t_ace3'),
        subtitle: L('s_ace3'),
        info: 'html/ace3.html'
    },
    AIMS: {
        task: 'task/Aims',
        title: L('b_aims'),
        tables: ['aims'],
        maintitle: L('t_aims'),
        subtitle: L('s_aims'),
        info: 'html/aims.html'
    },
    AUDIT: {
        task: 'task/Audit',
        title: L('b_audit'),
        tables: ['audit'],
        maintitle: L('t_audit'),
        subtitle: L('s_audit'),
        info: 'html/audit.html'
    },
    AUDIT_C: {
        task: 'task/AuditC',
        title: L('b_audit_c'),
        tables: ['audit_c'],
        maintitle: L('t_audit_c'),
        subtitle: L('s_audit_c'),
        info: 'html/audit.html'
    },
    BDI: {
        task: 'task/Bdi',
        title: L('b_bdi'),
        tables: ['bdi'],
        maintitle: L('t_bdi'),
        subtitle: L('s_bdi'),
        info: 'html/bdi.html'
    },
    BMI: {
        task: 'task/Bmi',
        title: L('b_bmi'),
        tables: ['bmi'],
        maintitle: L('t_bmi'),
        subtitle: L('s_bmi'),
        info: 'html/bmi.html'
    },
    BPRS: {
        task: 'task/Bprs',
        title: L('b_bprs'),
        tables: ['bprs'],
        maintitle: L('t_bprs'),
        subtitle: L('s_bprs'),
        info: 'html/bprs.html'
    },
    BPRSE: {
        task: 'task/BprsE',
        title: L('b_bprse'),
        tables: ['bprse'],
        maintitle: L('t_bprse'),
        subtitle: L('s_bprse'),
        info: 'html/bprse.html'
    },
    CAGE: {
        task: 'task/Cage',
        title: L('b_cage'),
        tables: ['cage'],
        maintitle: L('t_cage'),
        subtitle: L('s_cage'),
        info: 'html/cage.html'
    },
    CAPE42: {
        task: 'task/Cape42',
        title: L('b_cape42'),
        tables: ['cape42'],
        maintitle: L('t_cape42'),
        subtitle: L('s_cape42'),
        info: 'html/cape.html'
    },
    CAPS: {
        task: 'task/Caps',
        title: L('b_caps'),
        tables: ['caps'],
        maintitle: L('t_caps'),
        subtitle: L('s_caps'),
        info: 'html/caps.html'
    },
    CBI_R: {
        task: 'task/CbiR',
        title: L('b_cbir'),
        tables: ['cbir'],
        maintitle: L('t_cbir'),
        subtitle: L('s_cbir'),
        info: 'html/cbir.html'
    },
    CECAQ3: {
        task: 'task/CecaQ3',
        title: L('b_cecaq3'),
        tables: ['cecaq3'],
        maintitle: L('t_cecaq3'),
        subtitle: L('s_cecaq3'),
        info: 'html/cecaq3.html'
    },
    CGI: {
        task: 'task/Cgi',
        title: L('b_cgi'),
        tables: ['cgi'],
        maintitle: L('t_cgi'),
        subtitle: L('s_cgi'),
        info: 'html/cgi.html'
    },
    CGI_I: {
        task: 'task/CgiI',
        title: L('b_cgi_i'),
        tables: ['cgi_i'],
        maintitle: L('t_cgi_i'),
        subtitle: L('s_cgi_i'),
        info: 'html/from_lp.html'
    },
    CGISCH: {
        task: 'task/CgiSch',
        title: L('b_cgisch'),
        tables: ['cgisch'],
        maintitle: L('t_cgisch'),
        subtitle: L('s_cgisch'),
        info: 'html/cgisch.html'
    },
    CIWA: {
        task: 'task/Ciwa',
        title: L('b_ciwa'),
        tables: ['ciwa'],
        maintitle: L('t_ciwa'),
        subtitle: L('s_ciwa'),
        info: 'html/ciwa.html'
    },
    CONTACTLOG: {
        task: 'task/ContactLog',
        title: L('b_contactlog'),
        tables: ['contactlog'],
        maintitle: L('t_contactlog'),
        subtitle: L('s_contactlog'),
        info: 'html/clinical.html'
    },
    COPE_BRIEF: {
        task: 'task/CopeBrief',
        title: L('b_copebrief'),
        tables: ['cope_brief'],
        maintitle: L('t_copebrief'),
        subtitle: L('s_copebrief'),
        info: 'html/cope.html'
    },
    CPFT_LPS_DISCHARGE: {
        task: 'task/CPFT_LPS_Discharge',
        title: L('b_cpft_lps_discharge'),
        tables: ['cpft_lps_discharge'],
        maintitle: L('t_cpft_lps_discharge'),
        subtitle: L('s_cpft_lps_discharge'),
        info: 'html/clinical.html'
    },
    CPFT_LPS_REFERRAL: {
        task: 'task/CPFT_LPS_Referral',
        title: L('b_cpft_lps_referral'),
        tables: ['cpft_lps_referral'],
        maintitle: L('t_cpft_lps_referral'),
        subtitle: L('s_cpft_lps_referral'),
        info: 'html/clinical.html'
    },
    CPFT_LPS_RESETRESPONSECLOCK: {
        task: 'task/CPFT_LPS_ResetResponseClock',
        title: L('b_cpft_lps_resetresponseclock'),
        tables: ['cpft_lps_resetresponseclock'],
        maintitle: L('t_cpft_lps_resetresponseclock'),
        subtitle: L('s_cpft_lps_resetresponseclock'),
        info: 'html/clinical.html'
    },
    DAST: {
        task: 'task/Dast',
        title: L('b_dast'),
        tables: ['dast'],
        maintitle: L('t_dast'),
        subtitle: L('s_dast'),
        info: 'html/dast.html'
    },
    DEAKIN_1_HEALTHREVIEW: {
        task: 'task/Deakin_1_HealthReview',
        title: L('b_deakin_1_healthreview'),
        tables: ['deakin_1_healthreview'],
        maintitle: L('t_deakin_1_healthreview'),
        subtitle: L('s_deakin_1_healthreview'),
        info: 'html/deakin_1.html'
    },
    DEMOQUESTIONNAIRE: {
        task: 'task/DemoQuestionnaire',
        title: L('b_demo_task'),
        tables: ['demoquestionnaire'],
        maintitle: L('t_demo_task'),
        subtitle: L('s_demo_task'),
        info: 'html/demo_questionnaire.html'
    },
    DEMQOL: {
        task: 'task/Demqol',
        title: L('b_demqol'),
        tables: ['demqol'],
        maintitle: L('t_demqol'),
        subtitle: L('s_demqol'),
        info: 'html/demqol.html'
    },
    DEMQOL_PROXY: {
        task: 'task/DemqolProxy',
        title: L('b_demqolproxy'),
        tables: ['demqolproxy'],
        maintitle: L('t_demqolproxy'),
        subtitle: L('s_demqolproxy'),
        info: 'html/demqol.html'
    },
    DIAGNOSIS_ICD10: {
        task: 'task/DiagnosisIcd10',
        title: L('b_diagnosis_icd10'),
        tables: ['diagnosis_icd10',
                 'diagnosis_icd10_item'],
        maintitle: L('t_diagnosis_icd10'),
        subtitle: L('s_diagnosis_icd10'),
        info: 'html/icd.html'
    },
    DIAGNOSIS_ICD9CM: {
        task: 'task/DiagnosisIcd9CM',
        title: L('b_diagnosis_icd9cm'),
        tables: ['diagnosis_icd9cm',
                 'diagnosis_icd9cm_item'],
        maintitle: L('t_diagnosis_icd9cm'),
        subtitle: L('s_diagnosis_icd9cm'),
        info: 'html/icd.html'
    },
    DISTRESSTHERMOMETER: {
        task: 'task/DistressThermometer',
        title: L('b_distressthermometer'),
        tables: ['distressthermometer'],
        maintitle: L('t_distressthermometer'),
        subtitle: L('s_distressthermometer'),
        info: 'html/distressthermometer.html'
    },
    EXPDETTHRESHOLD: {
        task: 'task/Cardinal_ExpDetThreshold',
        title: L('b_expdetthreshold'),
        tables: ['cardinal_expdetthreshold',
                 'cardinal_expdetthreshold_trials'],
        maintitle: L('t_expdetthreshold'),
        subtitle: L('s_expdetthreshold'),
        info: 'html/cardinal_expdetthreshold.html'
    },
    EXPECTATIONDETECTION: {
        task: 'task/Cardinal_ExpectationDetection',
        title: L('b_expectationdetection'),
        tables: ['cardinal_expdet',
                 'cardinal_expdet_trialgroupspec',
                 'cardinal_expdet_trials'],
        maintitle: L('t_expectationdetection'),
        subtitle: L('s_expectationdetection'),
        info: 'html/cardinal_expdet_info.html'
    },
    FAST: {
        task: 'task/Fast',
        title: L('b_fast'),
        tables: ['fast'],
        maintitle: L('t_fast'),
        subtitle: L('s_fast'),
        info: 'html/fast.html'
    },
    FFT: {
        task: 'task/Fft',
        title: L('b_fft'),
        tables: ['fft'],
        maintitle: L('t_fft'),
        subtitle: L('s_fft'),
        info: 'html/from_lp.html'
    },
    GAD7: {
        task: 'task/Gad7',
        title: L('b_gad7'),
        tables: ['gad7'],
        maintitle: L('t_gad7'),
        subtitle: L('s_gad7'),
        info: 'html/gad7.html'
    },
    GAF: {
        task: 'task/Gaf',
        title: L('b_gaf'),
        tables: ['gaf'],
        maintitle: L('t_gaf'),
        subtitle: L('s_gaf'),
        info: 'html/gaf.html'
    },
    GDS15: {
        task: 'task/Gds15',
        title: L('b_gds15'),
        tables: ['gds15'],
        maintitle: L('t_gds15'),
        subtitle: L('s_gds15'),
        info: 'html/gds.html'
    },
    GMCPQ: {
        task: 'task/GmcPq',
        title: L('b_gmcpq'),
        tables: ['gmcpq'],
        maintitle: L('t_gmcpq'),
        subtitle: L('s_gmcpq'),
        info: 'html/gmc_patient_questionnaire.html'
    },
    HADS: {
        task: 'task/Hads',
        title: L('b_hads'),
        tables: ['hads'],
        maintitle: L('t_hads'),
        subtitle: L('s_hads'),
        info: 'html/hads.html'
    },
    HAMA: {
        task: 'task/HamA',
        title: L('b_hama'),
        tables: ['hama'],
        maintitle: L('t_hama'),
        subtitle: L('s_hama'),
        info: 'html/hama.html'
    },
    HAMD7: {
        task: 'task/HamD7',
        title: L('b_hamd7'),
        tables: ['hamd7'],
        maintitle: L('t_hamd7'),
        subtitle: L('s_hamd7'),
        info: 'html/hamd.html'
    },
    HAMD: {
        task: 'task/HamD',
        title: L('b_hamd'),
        tables: ['hamd'],
        maintitle: L('t_hamd'),
        subtitle: L('s_hamd'),
        info: 'html/hamd.html'
    },
    HONOS: {
        task: 'task/Honos',
        title: L('b_honos'),
        tables: ['honos'],
        maintitle: L('t_honos'),
        subtitle: L('s_honos'),
        info: 'html/honos.html'
    },
    HONOS65: {
        task: 'task/Honos65',
        title: L('b_honos65'),
        tables: ['honos65'],
        maintitle: L('t_honos65'),
        subtitle: L('s_honos65'),
        info: 'html/honos.html'
    },
    HONOSCA: {
        task: 'task/Honosca',
        title: L('b_honosca'),
        tables: ['honosca'],
        maintitle: L('t_honosca'),
        subtitle: L('s_honosca'),
        info: 'html/honos.html'
    },
    ICD10_DEPRESSIVE_EPISODE: {
        task: 'task/Icd10Depressive',
        title: L('b_icd10_depressive_episode'),
        tables: ['icd10depressive'],
        maintitle: L('t_icd10_depressive_episode'),
        subtitle: L('s_icd10'),
        info: 'html/icd.html'
    },
    ICD10_MANIC_EPISODE: {
        task: 'task/Icd10Manic',
        title: L('b_icd10_manic_episode'),
        tables: ['icd10manic'],
        maintitle: L('t_icd10_manic_episode'),
        subtitle: L('s_icd10'),
        info: 'html/icd.html'
    },
    ICD10_MIXED_EPISODE: {
        task: 'task/Icd10Mixed',
        title: L('b_icd10_mixed_episode'),
        tables: ['icd10mixed'],
        maintitle: L('t_icd10_mixed_episode'),
        subtitle: L('s_icd10'),
        info: 'html/icd.html'
    },
    ICD10_SCHIZOPHRENIA: {
        task: 'task/Icd10Schizophrenia',
        title: L('b_icd10_schizophrenia'),
        tables: ['icd10schizophrenia'],
        maintitle: L('t_icd10_schizophrenia'),
        subtitle: L('s_icd10'),
        info: 'html/icd.html'
    },
    ICD10_SCHIZOTYPAL: {
        task: 'task/Icd10Schizotypal',
        title: L('b_icd10_schizotypal'),
        tables: ['icd10schizotypal'],
        maintitle: L('t_icd10_schizotypal'),
        subtitle: L('s_icd10'),
        info: 'html/icd.html'
    },
    ICD10_SPECIFIC_PD: {
        task: 'task/Icd10SpecPD',
        title: L('b_icd10_specific_pd'),
        tables: ['icd10specpd'],
        maintitle: L('t_icd10_specific_pd'),
        subtitle: L('s_icd10'),
        info: 'html/icd.html'
    },
    IDED3D: {
        task: 'task/IDED3D',
        title: L('b_ided3d'),
        tables: ['ided3d', 'ided3d_stages', 'ided3d_trials'],
        maintitle: L('t_ided3d'),
        subtitle: L('s_ided3d'),
        info: 'html/ided3d.html'
    },
    IESR: {
        task: 'task/Iesr',
        title: L('b_iesr'),
        tables: ['iesr'],
        maintitle: L('t_iesr'),
        subtitle: L('s_iesr'),
        info: 'html/iesr.html'
    },
    IRAC: {
        task: 'task/Irac',
        title: L('b_irac'),
        tables: ['irac'],
        maintitle: L('t_irac'),
        subtitle: L('s_irac'),
        info: 'html/from_lp.html'
    },
    MAST: {
        task: 'task/Mast',
        title: L('b_mast'),
        tables: ['mast'],
        maintitle: L('t_mast'),
        subtitle: L('s_mast'),
        info: 'html/mast.html'
    },
    MDS_UPDRS: {
        task: 'task/MdsUpdrs',
        title: L('b_mds_updrs'),
        tables: ['mds_updrs'],
        maintitle: L('t_mds_updrs'),
        subtitle: L('s_mds_updrs'),
        info: 'html/mds.html'
    },
    MOCA: {
        task: 'task/Moca',
        title: L('b_moca'),
        tables: ['moca'],
        maintitle: L('t_moca'),
        subtitle: L('s_moca'),
        info: 'html/moca.html'
    },
    NART: {
        task: 'task/Nart',
        title: L('b_nart'),
        tables: ['nart'],
        maintitle: L('t_nart'),
        subtitle: L('s_nart'),
        info: 'html/nart.html'
    },
    PANSS: {
        task: 'task/Panss',
        title: L('b_panss'),
        tables: ['panss'],
        maintitle: L('t_panss'),
        subtitle: L('s_panss'),
        info: 'html/panss.html'
    },
    PATIENT_SATISFACTION: {
        task: 'task/PatientSatisfaction',
        title: L('b_pt_satis'),
        tables: ['pt_satis'],
        maintitle: L('t_pt_satis'),
        subtitle: L('s_pt_satis'),
        info: 'html/from_lp.html'
    },
    PCLC: {
        task: 'task/PclC',
        title: L('b_pcl_c'),
        tables: ['pclc'],
        maintitle: L('t_pcl_c'),
        subtitle: L('s_pcl_c'),
        info: 'html/pcl.html'
    },
    PCLM: {
        task: 'task/PclM',
        title: L('b_pcl_m'),
        tables: ['pclm'],
        maintitle: L('t_pcl_m'),
        subtitle: L('s_pcl_m'),
        info: 'html/pcl.html'
    },
    PCLS: {
        task: 'task/PclS',
        title: L('b_pcl_s'),
        tables: ['pcls'],
        maintitle: L('t_pcl_s'),
        subtitle: L('s_pcl_s'),
        info: 'html/pcl.html'
    },
    PHOTO: {
        task: 'task/Photo',
        title: L('b_photo'),
        tables: ['photo'],
        maintitle: L('t_photo'),
        subtitle: L('s_photo'),
        info: 'html/clinical.html'
    },
    PHOTOSEQUENCE: {
        task: 'task/PhotoSequence',
        title: L('b_photosequence'),
        tables: ['photosequence',
                 'photosequence_photos'],
        maintitle: L('t_photosequence'),
        subtitle: L('s_photosequence'),
        info: 'html/clinical.html'
    },
    PHQ9: {
        task: 'task/Phq9',
        title: L('b_phq9'),
        tables: ['phq9'],
        maintitle: L('t_phq9'),
        subtitle: L('s_phq9'),
        info: 'html/phq9.html'
    },
    PHQ15: {
        task: 'task/Phq15',
        title: L('b_phq15'),
        tables: ['phq15'],
        maintitle: L('t_phq15'),
        subtitle: L('s_phq15'),
        info: 'html/phq15.html'
    },
    PROGRESSNOTE: {
        task: 'task/ProgressNote',
        title: L('b_progressnote'),
        tables: ['progressnote'],
        maintitle: L('t_progressnote'),
        subtitle: L('s_progressnote'),
        info: 'html/clinical.html'
    },
    PSYCHIATRICCLERKING: {
        task: 'task/PsychiatricClerking',
        title: L('b_psychiatricclerking'),
        tables: ['psychiatricclerking'],
        maintitle: L('t_psychiatricclerking'),
        subtitle: L('s_psychiatricclerking'),
        info: 'html/clinical.html'
    },
    QOLBASIC: {
        task: 'task/QoLBasic',
        title: L('b_qolbasic'),
        tables: ['qolbasic'],
        maintitle: L('t_qolbasic'),
        subtitle: L('s_qolbasic'),
        info: 'html/qol.html'
    },
    QOLSG: {
        task: 'task/QoLSG',
        title: L('b_qolsg'),
        tables: ['qolsg'],
        maintitle: L('t_qolsg'),
        subtitle: L('s_qolsg'),
        info: 'html/qol.html'
    },
    RAND36: {
        task: 'task/Rand36',
        title: L('b_rand36'),
        tables: ['rand36'],
        maintitle: L('t_rand36'),
        subtitle: L('s_rand36'),
        info: 'html/rand36.html'
    },
    REFERRER_SATISFACTION_GEN: {
        task: 'task/ReferrerSatisfactionGen',
        title: L('b_ref_satis_gen'),
        tables: ['ref_satis_gen'],
        maintitle: L('t_ref_satis_gen'),
        subtitle: L('s_ref_satis_gen'),
        info: 'html/from_lp.html'
    },
    REFERRER_SATISFACTION_SPEC: {
        task: 'task/ReferrerSatisfactionSpec',
        title: L('b_ref_satis_spec'),
        tables: ['ref_satis_spec'],
        maintitle: L('t_ref_satis_spec'),
        subtitle: L('s_ref_satis_spec'),
        info: 'html/from_lp.html'
    },
    SLUMS: {
        task: 'task/Slums',
        title: L('b_slums'),
        tables: ['slums'],
        maintitle: L('t_slums'),
        subtitle: L('s_slums'),
        info: 'html/slums.html'
    },
    SMAST: {
        task: 'task/Smast',
        title: L('b_smast'),
        tables: ['smast'],
        maintitle: L('t_smast'),
        subtitle: L('s_smast'),
        info: 'html/mast.html'  // shares its HTML
    },
    SWEMWBS: {
        task: 'task/Swemwbs',
        title: L('b_swemwbs'),
        tables: ['swemwbs'],
        maintitle: L('t_swemwbs'),
        subtitle: L('s_swemwbs'),
        info: 'html/wemwbs.html'  // shares its HTML
    },
    WEMWBS: {
        task: 'task/Wemwbs',
        title: L('b_wemwbs'),
        tables: ['wemwbs'],
        maintitle: L('t_wemwbs'),
        subtitle: L('s_wemwbs'),
        info: 'html/wemwbs.html'
    },
    ZBI12: {
        task: 'task/Zbi12',
        title: L('b_zbi12'),
        tables: ['zbi12'],
        maintitle: L('t_zbi12'),
        subtitle: L('s_zbi12'),
        info: 'html/zbi.html'
    }

    // Removed
    /*
    // NOT FREE // LSHSA: {
        task: 'task/LshsA',
        title: L('b_lshs_a'),
        tables: ['lshs_a'],
        maintitle: L('t_lshs_a'),
        subtitle: L('s_lshs_a'),
        info: 'html/lshs.html'
    },
    // BASED ON LSHS; PRESUMABLY NOT FREE // LSHSLAROI2005: {
        task: 'task/LshsLaroi2005',
        title: L('b_lshs_laroi2005'),
        tables: ['lshs_laroi2005'],
        maintitle: L('t_lshs_laroi2005'),
        subtitle: L('s_lshs_laroi2005'),
        info: 'html/lshs.html'},
        // shares HTML
    // PERMISSION REFUSED // BFCRS: {
        task: 'task/Bfcrs',
        title: L('b_bfcrs'),
        tables: ['bfcrs'],
        maintitle: L('t_bfcrs'),
        subtitle: L('s_bfcrs'),
        info: 'html/bfcrs.html'
    },
    // PERMISSION REFUSED // CSI: {
        task: 'task/Csi',
        title: L('b_csi'),
        tables: ['csi'],
        maintitle: L('t_csi'),
        subtitle: L('s_csi'),
        info: 'html/bfcrs.html'
    },
    // PERMISSION REFUSED // GASS: {
        task: 'task/Gass',
        title: L('b_gass'),
        tables: ['gass'],
        maintitle: L('t_gass'),
        subtitle: L('s_gass'),
        info: 'html/gass.html'
    },
    // PERMISSION REFUSED // LUNSERS: {
        task: 'task/Lunsers',
        title: L('b_lunsers'),
        tables: ['lunsers'],
        maintitle: L('t_lunsers'),
        subtitle: L('s_lunsers'),
        info: 'html/lunsers.html'
    },
    // PERMISSION REFUSED // SAS: {
        task: 'task/Sas',
        title: L('b_sas'),
        tables: ['sas'],
        maintitle: L('t_sas'),
        subtitle: L('s_sas'),
        info: 'html/sas.html'
    },
    // PERMISSION REFUSED // BARS: {
        copyrightDetailsPending:true,
        task: 'task/Bars',
        title: L('b_bars'),
        tables: ['bars'],
        maintitle: L('t_bars'),
        subtitle: L('s_bars'),
        info: 'html/bars.html'
    },
    // PERMISSION REFUSED // MADRS: {
        copyrightDetailsPending:true,
        task: 'task/Madrs',
        title: L('b_madrs'),
        tables: ['madrs'],
        maintitle: L('t_madrs'),
        subtitle: L('s_madrs'),
        info: 'html/madrs.html'
    },
    // PERMISSION REFUSED // FAB: {
        copyrightDetailsPending:true,
        task: 'task/Fab',
        title: L('b_fab'),
        tables: ['fab'],
        maintitle: L('t_fab'),
        subtitle: L('s_fab'),
        info: 'html/fab.html'
    },
    // PERMISSION REFUSED // EPDS: {
        task: 'task/Epds',
        title: L('b_epds'),
        tables: ['epds'],
        maintitle: L('t_epds'),
        subtitle: L('s_epds'),
        info: 'html/epds.html'
    },
    // PERMISSION REFUSED // ASRM: {
        copyrightDetailsPending:true,
        task: 'task/Asrm',
        title: L('b_asrm'),
        tables: ['asrm'],
        maintitle: L('t_asrm'),
        subtitle: L('s_asrm'),
        info: 'html/asrm.html'
    },
    */
};
