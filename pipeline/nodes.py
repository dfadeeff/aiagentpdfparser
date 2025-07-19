import re
from typing import Dict, Any, List, Tuple
from pipeline.state import PipelineState
from tools.extractor import extract_values_from_pdf, get_all_text_elements


def extraction_node(state: PipelineState) -> Dict[str, Any]:
    """
    NODE 1: Extract numeric values and text elements from PDF (unchanged).
    """
    print("\n🔍 NODE 1: EXTRACTION")
    print("-" * 40)
    pdf_path = state["pdf_path"]
    values = extract_values_from_pdf(pdf_path)
    all_text = get_all_text_elements(pdf_path)
    print(f"✅ Extracted {len(values)} numeric values")
    print(f"✅ Found {len(all_text)} total text elements")
    return {"extracted_values": values, "all_text_elements": all_text}


def split_by_largest_gaps(
    elems: List[Dict[str, Any]], coord: str, k: int
) -> List[List[Dict[str, Any]]]:
    """
    Split elems into k clusters along 1D coordinate ('x' or 'y') by finding the k-1 largest gaps.
    coord: 'x' means midpoint of x0,x1; 'y' means midpoint of y0,y1.
    """
    # compute sorted list of (center, elem)
    centers: List[Tuple[float, Dict[str, Any]]] = []
    for e in elems:
        if coord == 'x':
            c = (e['bbox']['x0'] + e['bbox']['x1']) / 2
        else:
            c = (e['bbox']['y0'] + e['bbox']['y1']) / 2
        centers.append((c, e))
    centers.sort(key=lambda x: x[0])

    if len(centers) <= k:
        # each element its own cluster if fewer than k
        return [[e] for _, e in centers]

    # compute gaps
    gaps: List[Tuple[float,int]] = []  # (gap_size, index)
    for i in range(len(centers) - 1):
        gap = centers[i+1][0] - centers[i][0]
        gaps.append((gap, i))
    # pick k-1 largest gaps
    largest = sorted(gaps, key=lambda x: x[0], reverse=True)[:k-1]
    split_indices = sorted(idx for _, idx in largest)

    # split at these indices
    clusters: List[List[Dict[str, Any]]] = []
    prev = 0
    for idx in split_indices:
        cluster = [e for _, e in centers[prev:idx+1]]
        clusters.append(cluster)
        prev = idx+1
    # last cluster
    clusters.append([e for _, e in centers[prev:]])
    return clusters


def metadata_enrichment_node(state: PipelineState) -> Dict[str, Any]:
    """
    NODE 2: Extract row and column headers via spatial clustering into
    exactly 4 row levels and 3 column levels.

    1) Normalize and filter all text elements.
    2) Compute table data-region bounds from values.
    3) Select header candidates: above table for columns, left of table for rows.
    4) Cluster row candidates into 4 X-clusters, col candidates into 3 Y-clusters.
    5) For each cell, pick one header from each cluster level by bbox overlap.
    """
    print("\n📊 NODE 2: METADATA ENRICHMENT (CLUSTERED LEVELS)")
    print("-" * 40)
    values = state["extracted_values"]
    all_text = state["all_text_elements"]

    # 1) Normalize & filter
    ocr_map = {
        'colt': 'Col1', 'colta': 'Col1',
        'col2a': 'Col2A', 'col2b': 'Col2B',
        'col4a': 'Col4A', 'col4b': 'Col4B',
        'eo': None, 'eas': None, 'coms': None
    }
    def normalize(txt: str) -> str:
        t = txt.strip()
        key = t.lower()
        if key in ocr_map:
            return ocr_map[key] or ''
        return t
    def is_header(txt: str) -> bool:
        t = normalize(txt)
        return bool(t) and not re.match(r'^\d+([.,]\d+)?$', t)

    headers_all: List[Dict[str, Any]] = []
    for e in all_text:
        norm = normalize(e['text'])
        if is_header(e['text']):
            headers_all.append({**e, 'norm': norm})

    # 2) Data region bounds
    min_val_y = min(v['bbox']['y0'] for v in values)
    min_val_x = min(v['bbox']['x0'] for v in values)

    # 3) Candidates
    col_candidates = [e for e in headers_all
                      if (e['bbox']['y1'] < min_val_y)]
    row_candidates = [e for e in headers_all
                      if (e['bbox']['x1'] < min_val_x)]

    # 4) Cluster
    row_levels = split_by_largest_gaps(row_candidates, coord='x', k=4)
    col_levels = split_by_largest_gaps(col_candidates, coord='y', k=3)

    # 5) Assign
    enriched: List[Dict[str, Any]] = []
    for v in values:
        bbox = v['bbox']
        vcx = (bbox['x0'] + bbox['x1']) / 2
        vcy = (bbox['y0'] + bbox['y1']) / 2
        row_hdrs: List[str] = []
        col_hdrs: List[str] = []

        # one per row level
        for lvl in row_levels:
            for e in lvl:
                if e['bbox']['y0'] <= vcy <= e['bbox']['y1']:
                    row_hdrs.append(e['norm'])
                    break
        # one per col level
        for lvl in col_levels:
            for e in lvl:
                if e['bbox']['x0'] <= vcx <= e['bbox']['x1']:
                    col_hdrs.append(e['norm'])
                    break

        enriched.append({
            'value': v['value'],
            'row_headers': row_hdrs,
            'column_headers': col_hdrs,
            'confidence': v['confidence'],
            'bbox': bbox
        })

    print(f"✅ Enriched metadata for {len(enriched)} values")
    return {'values_with_metadata': enriched}


def cleaning_node(state: PipelineState) -> Dict[str, Any]:
    """
    NODE 3: Deduplicate and finalize headers
    """
    print("\n🧹 NODE 3: CLEANING & FINALIZATION")
    print("-" * 40)
    out = []
    for v in state['values_with_metadata']:
        rh = list(dict.fromkeys(v['row_headers']))
        ch = list(dict.fromkeys(v['column_headers']))
        out.append({**v, 'row_headers': rh, 'column_headers': ch})
    print(f"✅ Cleaned {len(out)} values")
    return {'values_with_metadata': out}
