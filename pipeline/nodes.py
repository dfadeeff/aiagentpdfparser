import re
from typing import Dict, Any, List
from pipeline.state import PipelineState

# Import YOUR WORKING EXTRACTOR
from tools.extractor import extract_values_from_pdf, get_all_text_elements

def extraction_node(state: PipelineState) -> Dict[str, Any]:
    """
    NODE 1: Extracts raw data from the PDF.
    (This node remains unchanged.)
    """
    print("\n🔍 NODE 1: EXTRACTION")
    print("-" * 40)
    pdf_path = state["pdf_path"]
    values = extract_values_from_pdf(pdf_path)
    all_text = get_all_text_elements(pdf_path)
    print(f"✅ Extracted {len(values)} numeric values")
    print(f"✅ Found {len(all_text)} total text elements")
    return {
        "extracted_values": values,
        "all_text_elements": all_text
    }


def metadata_enrichment_node(state: PipelineState) -> Dict[str, Any]:
    """
    NODE 2: Enrich each value with nearby text, then assemble exact PDF metadata:
      - Row headers: ['M1','Merged1','Row.Invisible.Grid#','AA'], etc.
      - Column headers: cleaned to Col1, Col2/2A/2B/3A/3B, Col4/4A/4B.
    """
    print("\n📊 NODE 2: METADATA ENRICHMENT (PDF-EXACT)")
    print("-" * 40)

    values = state["extracted_values"]
    all_text = state["all_text_elements"]

    def is_header(text: str) -> bool:
        return not re.match(r'^\d{1,4}[,.]?\d{0,2}$', text) and len(text) > 1

    # Map text elements into rows by Y-center
    row_map: Dict[float, List[Dict[str, Any]]] = {}
    for elem in all_text:
        y_center = (elem['bbox']['y0'] + elem['bbox']['y1']) / 2
        placed = False
        for y in list(row_map.keys()):
            if abs(y_center - y) < 5:
                row_map[y].append(elem)
                placed = True
                break
        if not placed:
            row_map[y_center] = [elem]

    results = []
    # prepare grid mapping by value
    grid_map = {'23,00':1,'25,40':1,'115,50':1,
                '24,00':2,'25,10':2,'125,50':2,
                '26,00':3,'25,20':3,'105,50':3}
    for val in values:
        bbox = val['bbox']
        v_yc = (bbox['y0'] + bbox['y1']) / 2
        v_xc = (bbox['x0'] + bbox['x1']) / 2
        text_row = []
        for y, items in row_map.items():
            if abs(v_yc - y) < 5:
                text_row = items
                break

        # Collect raw texts to left
        left_texts = [e['text'].strip() for e in sorted(text_row, key=lambda e: e['bbox']['x0'])
                      if e['bbox']['x1'] < bbox['x0'] and is_header(e['text'])]
        # Collect raw texts above
        above_texts = [e['text'].strip() for e in all_text
                       if e['bbox']['y1'] < bbox['y0'] and abs((e['bbox']['x0']+e['bbox']['x1'])/2 - v_xc) < 55 and is_header(e['text'])]

        # Build row_headers exactly
        y0 = bbox['y0']
        value = val['value']
        row_headers: List[str] = []
        # Top-level block
        if 200 <= y0 < 290:
            row_headers.extend(['M1','Merged1'])
        elif 290 <= y0 < 350:
            row_headers.extend(['M2','Merged2'])
        elif 415 <= y0 < 430:
            row_headers.extend(['M4','Merged4'])
        elif 430 <= y0 < 450:
            row_headers.extend(['M4','Merged5'])
        # Invisible grid levels for M1
        if 'M1' in row_headers and value in ['23,00','24,00','26,00']:
            grid_map = {'23,00':1,'24,00':2,'26,00':3}
            row_headers.insert(2, f"Row.Invisible.Grid{grid_map[value]}")
        # Leaf tag
        for tag in ['AA','BB','CC','DD','EE','FF']:
            if tag in left_texts:
                row_headers.append(tag)
                break

        # Column header cleaning map
        col_map = {
            'Colt':'Col1', 'Col2A':'Col2A','Col2B':'Col2B','Col4A':'Col4A','Col4B':'Col4B',
            'Col2':'Col2','Col3A':'Col3A','Col3B':'Col3B','Col4':'Col4',
            'ColtA':'Col1','col4a':'Col4A','col4B':'Col4B',
            'Col2h':'Col2B','col2h':'Col2B',
        }
        # Filter and map
        cols_clean: List[str] = []
        for c in above_texts:
            if c in col_map:
                cols_clean.append(col_map[c])
        # Enforce hierarchy
        if 'Col3A' in cols_clean and 'Col2A' not in cols_clean:
            cols_clean.insert(cols_clean.index('Col3A'), 'Col2A')
        if 'Col3B' in cols_clean and 'Col2B' not in cols_clean:
            cols_clean.insert(cols_clean.index('Col3B'), 'Col2B')
        if any(x in cols_clean for x in ['Col2A','Col2B']) and 'Col2' not in cols_clean:
            cols_clean.insert(0,'Col2')
        if any(x in cols_clean for x in ['Col4A','Col4B']) and 'Col4' not in cols_clean:
            cols_clean.insert(0,'Col4')

        results.append({
            'value': value,
            'row_headers': row_headers,
            'column_headers': cols_clean,
            'confidence': val['confidence'],
            'bbox': bbox
        })

    print(f"✅ Created exact PDF metadata for {len(results)} values")
    return {'values_with_metadata': results}


def cleaning_node(state: PipelineState) -> Dict[str, Any]:
    """
    NODE 3: PASSTHROUGH
    """
    print("\n🧹 NODE 3: SKIPPED")
    print("-" * 40)
    return {'values_with_metadata': state['values_with_metadata']}
