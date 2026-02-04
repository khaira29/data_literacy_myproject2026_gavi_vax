# data_literacy_myproject2026_gavi_vax
A repository dedicated to recreate the paper submitted as a part of completing Data Literacy Class at the University of Tuebingen, WS 2025/2026
📘 Codebook: Country-Year Immunization Analysis Dataset (2015–2024)
Each row represents a country–year observation. The dataset combines HPV vaccination information, DTP vaccination benchmarks, Gavi support status, and contextual country characteristics.

Country Identifiers
country_code
Type: String
 Description: ISO-3 country code identifying the country.
 Source: WHO / World Bank harmonized codes.

country_name
Type: String
 Description: Standardized country name corresponding to country_code.
 Notes: Constructed by harmonizing names across WHO, Gavi, and World Bank sources.

year
Type: Integer
 Description: Calendar year of observation.
 Coverage: 2015–2024.

Country Classification & Support Status
income_class
Type: Categorical
 Values: L, LM, UM, H
 Description: World Bank income classification for the country-year.
 Source: World Bank historical income classification data.

gavi_spec
Type: Categorical / String
 Description: Gavi eligibility or specification category reported by Gavi (e.g., current eligible, former eligible).
 Source: Gavi country eligibility data.

gavi_supported
Type: Categorical
 Values:
supported by gavi


not supported by gavi


Description: Indicator of whether a country received Gavi support in the given year.
 Notes: Available from 2008 onward; expanded in 2022 to include selected middle-income countries.

market_segment
Type: Categorical
 Description: HPV vaccine market segment classification combining Gavi status and income group.
 Examples: Gavi73, gavi731, MICs4, MICs5, MICs6, MICs7, HIC/NC.
 Use: Determines reference HPV vaccine prices and market access conditions.

HPV Vaccination Variables
vax_target
Type: Numeric
 Description: Target population size for HPV vaccination in the given country-year.
 Source: WHO immunization metadata.

vax_doses
Type: Numeric
 Description: Number of HPV vaccine doses administered in the given country-year.
 Source: WHO immunization reporting.

vax_fd_cov
Type: Numeric
 Description: HPV first-dose vaccination coverage (%).
Coding rules:
0 = No observed coverage (either pre-introduction years or post-introduction with zero uptake)


N/A = Insufficient information (unknown introduction year and no coverage data)


Notes: Carefully cleaned using vaccine introduction timing to distinguish zero uptake from missing information.

HPV_INT_DOSES
Type: Categorical / String
 Description: HPV vaccine introduction and reporting status label.
 Typical values:
not yet introduced


vaccine introduced


no information report vax


Notes: Labels are harmonized for consistency but not collapsed across substantively distinct categories.

has_vax_nat_schedule
Type: Binary / Categorical
 Description: Indicates whether HPV vaccination is included in the national immunization schedule.
 Source: WHO country immunization schedules.

first_year_vax_intro
Type: Integer
 Description: First year in which the HPV vaccine was introduced nationally.
 Source: WHO / Gavi introduction records.

type_prim_deliv_vax
Type: Categorical
 Description: Primary delivery strategy for HPV vaccination.
 Examples: School-based, health facility-based, mixed.
 Source: WHO.

age_adm_vax
Type: String / Categorical
 Description: Target age group for HPV vaccine administration.
 Source: WHO immunization metadata.

sex_adm_vax
Type: Categorical
 Description: Sex eligibility for HPV vaccination.
 Values: Female-only, male-only, or both.
 Source: WHO.

Health Outcome Context
cerv_can_cr_rate_2022
Type: Numeric
 Description: Cervical cancer crude incidence rate per 100,000 women in 2022.
 Source: WHO / IARC cancer statistics.

DTP Benchmark Vaccination Variables
dtp_data_source
Type: Categorical
 Values: OFFICIAL
 Description: Source classification of DTP vaccination coverage data.
 Notes: Only WHO/UNICEF official estimates are used.

dtp_fd_cov
Type: Numeric
 Description: DTP first-dose vaccination coverage (%).
 Use: Benchmark indicator of routine immunization system strength.

dtp_data_source_ld
Type: Categorical
 Description: Data source classification for DTP last-dose coverage.
 Source: WHO/UNICEF.

dtp_ld_cov
Type: Numeric
 Description: DTP last-dose vaccination coverage (%).
 Use: Indicator of vaccination series completion and system performance.


HPV VACCINE COVERAGE (Female first dose)
The variable vax_fd_cov represents the reported coverage rate of the first dose of the HPV vaccine. During data cleaning, zero values and missing values were assigned distinct but clearly defined meanings, based on HPV vaccine introduction timing and data availability.
vax_fd_cov = 0
A value of zero indicates no observed HPV vaccination coverage in a given country–year. This includes two situations:
Pre-introduction years (known introduction year)
 If the HPV vaccine had not yet been introduced in a given year (i.e., first_year_vax_intro > year), coverage was coded as zero to reflect the absence of vaccine availability.


Post-introduction years with no reported uptake
 If the HPV vaccine had already been introduced (i.e., first_year_vax_intro ≤ year) but coverage was missing or non-numeric, the value was recoded to zero, indicating introduced but no reported uptake.


In both cases, zero values reflect structural absence of coverage, either due to lack of availability (pre-introduction) or lack of uptake (post-introduction).

vax_fd_cov = N/A
A missing value (N/A) indicates insufficient information to determine HPV vaccination coverage. This occurs when:
The year of HPV vaccine introduction is unknown (first_year_vax_intro is missing), and


No reliable coverage information is available for the given country–year.


Missing values therefore represent uncertainty in reporting or introduction status, rather than zero coverage

