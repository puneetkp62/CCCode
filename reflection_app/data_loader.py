import pandas as pd

ROLE_FUNCTION_SHEET_MAP = {
    'Institutional sales': 'Institutional Sales V01',
    'Institutional Sales': 'Institutional Sales V01',
    'Channel Sales': 'Channel Sales V02',
    'High Value Sales': 'High Value Sales V03',
    'Business Development': 'Business Development V04',
    'International Business': 'International Business V05',
    'Application': 'Applications V06',
    'Applications': 'Applications V06',
    'Marketing': 'MarketingV07',
    'Engineering Services': 'Eningeering ServicesV08 ',
    'Projects': 'ProjectsV09',
    'SCM Planning': 'SCM PlanningV10',
    'SCM Procurement': 'SCM ProcurementV11',
    'R&D': 'R&DV12',
    'Marcom': 'MarcomV13',
    'MARCOM': 'MarcomV13',
    'SCM Logistics': 'SCM LogisticsV14',
    'Admin': 'AdminV15',
    'HR': 'HRV16',
    'L&D': 'L&DV17',
    'IT': 'ITV18',
    'FACT': 'FACTV19',
}

GENERAL_QUESTIONS = [
    "Looking back over the last 3 years, what are 2 or 3 contributions or accomplishments you feel most proud of?",
    "What kind of work gives you the greatest sense of energy, satisfaction or meaning?",
    "In the last 3 years what efforts have you made to acquire new learnings and new skills?",
    "What challenges or experiences have contributed most to your growth?",
    "What part of your work did you find the most challenging over the last one year?",
    "Which competencies would you like to strengthen in future to be able to deliver your work better?",
    "What kind of work, responsibilities or opportunities would you like to explore going ahead?",
    "What kind of support or exposure will help you grow most effectively in the future?",
    "Who would you like to have as your mentor/coach in the organisation (give 3 options)?",
]

EXPLORE_OPTIONS = [
    "Building deeper technical or functional expertise",
    "Cross-functional/business exposure",
    "Strategic/project-based roles",
    "Customer-facing/business growth roles",
    "Still exploring and not fully sure yet",
]

BANDS = ['FT', 'FMT', 'OMT', 'BMT', 'SMT']


def load_employee_data():
    df = pd.read_excel('data/employee_data.xlsx', sheet_name='Data')
    df = df.dropna(subset=['Emp Code'])
    employees = []
    employee_dict = {}
    for _, row in df.iterrows():
        raw_code = row['Emp Code']
        emp_code = str(int(raw_code)) if isinstance(raw_code, float) else str(raw_code).strip()
        emp = {
            'emp_code': emp_code,
            'emp_name': str(row['Emp Name']).strip() if pd.notna(row.get('Emp Name')) else '',
            'role': str(row['Role']).strip() if pd.notna(row.get('Role')) else '',
            'team_leader': str(row['Team Leader']).strip() if pd.notna(row.get('Team Leader')) else '',
            'core_group': str(row['Core Group']).strip() if pd.notna(row.get('Core Group')) else '',
            'division': str(row['Division']).strip() if pd.notna(row.get('Division')) else '',
            'vertical': str(row['Vertical']).strip() if pd.notna(row.get('Vertical')) else '',
            'role_function': str(row['Role Function']).strip() if pd.notna(row.get('Role Function')) else '',
        }
        employees.append(emp)
        employee_dict[emp_code] = emp
    return employees, employee_dict


def load_competencies():
    return pd.read_excel('data/competencies.xlsx', sheet_name=None, header=None)


def _find_band_indicator_col(raw_df, band):
    """
    Sheet layout (all function sheets follow this):
      row1 = band names  (FT, FMT, OMT, BMT, SMT) — some sheets have Level cols in between
      row2 = col headers (Sr No., Competency, Attribute, Description, Indicator …)
      row3+ = data
    Strategy:
      1. Collect band→col from row1
      2. Collect indicator col positions from row2
      3. For each band, its indicator col is the nearest Indicator col at or after the band col,
         but before the next band col.
    """
    row1 = raw_df.iloc[1].tolist()
    row2 = raw_df.iloc[2].tolist()

    band_upper = band.strip().upper()

    # Map band name → col index from row1
    band_cols = {}
    all_bands = ['FT', 'FMT', 'OMT', 'BMT', 'SMT']
    for col_idx, val in enumerate(row1):
        if isinstance(val, str):
            v = val.strip().upper()
            if v in all_bands and v not in band_cols:
                band_cols[v] = col_idx

    if band_upper not in band_cols:
        return None

    target_col = band_cols[band_upper]

    # Find next band col (upper bound)
    sorted_band_cols = sorted(band_cols.values())
    next_col = len(row2)
    for bc in sorted_band_cols:
        if bc > target_col:
            next_col = bc
            break

    # Find Indicator columns within [target_col, next_col)
    for col_idx in range(target_col, min(next_col, len(row2))):
        cell = row2[col_idx]
        if isinstance(cell, str) and 'indicator' in cell.lower():
            return col_idx

    # Fallback: the band col itself if row2 says Indicator
    if isinstance(row2[target_col], str) and 'indicator' in row2[target_col].lower():
        return target_col

    return target_col


def get_competencies_for_role_band(sheets, role_function, band):
    rf_clean = role_function.strip()
    sheet_name = ROLE_FUNCTION_SHEET_MAP.get(rf_clean)

    if not sheet_name or sheet_name not in sheets:
        for key, val in ROLE_FUNCTION_SHEET_MAP.items():
            if key.lower() == rf_clean.lower() and val in sheets:
                sheet_name = val
                break

    if not sheet_name or sheet_name not in sheets:
        return []

    raw_df = sheets[sheet_name]
    indicator_col = _find_band_indicator_col(raw_df, band)
    if indicator_col is None:
        return []

    competencies = []
    last_competency = ''

    # Data starts at row 3 (rows 0-2 are metadata/headers)
    for row_idx in range(3, len(raw_df)):
        row = raw_df.iloc[row_idx]

        comp_val = row.iloc[1]
        if pd.notna(comp_val) and str(comp_val).strip():
            v = str(comp_val).strip()
            if v.lower() not in ('competency', 'competency '):
                last_competency = v

        attribute = str(row.iloc[2]).strip() if pd.notna(row.iloc[2]) else ''
        description = str(row.iloc[3]).strip() if pd.notna(row.iloc[3]) else ''

        indicator = ''
        if indicator_col < len(row):
            raw_ind = row.iloc[indicator_col]
            indicator = str(raw_ind).strip() if pd.notna(raw_ind) else ''

        indicator = indicator.replace('\n', ' ').strip()
        description = description.replace('\n', ' ').strip()

        skip_words = ('attribute', 'indicator', 'description', 'discription',
                      'attribute ', 'indicator ', 'description ')
        if not attribute and not indicator:
            continue
        if attribute.strip().lower() in skip_words:
            continue

        competencies.append({
            'competency': last_competency,
            'attribute': attribute,
            'description': description,
            'indicator': indicator,
        })

    return competencies
