"""
Create a test PDF with distinctive, verifiable content.
Upload it to the existing notebook (ID=1).
Test the RAG chat endpoint with questions whose answers can be verified.
"""
import requests
import json
import os
import sys
from fpdf import FPDF

BASE = 'http://127.0.0.1:8000'
NB_ID = 1

# Step 1: Create a test PDF with distinctive facts
print('=== Step 1: Create test PDF ===')
pdf = FPDF()
pdf.add_page()
pdf.set_font('Helvetica', 'B', 18)
pdf.cell(0, 12, 'The Aurora Protocol: A Framework for', ln=True, align='C')
pdf.cell(0, 12, 'Distributed Quantum Computing', ln=True, align='C')
pdf.set_font('Helvetica', '', 10)
pdf.cell(0, 8, 'Dr. Elena Vasquez, Institute for Advanced Computation, 2025', ln=True, align='C')
pdf.ln(8)

pdf.set_font('Helvetica', 'B', 14)
pdf.cell(0, 10, 'Abstract', ln=True)
pdf.set_font('Helvetica', '', 11)
abstract = (
    "The Aurora Protocol introduces a novel framework for distributed quantum computing "
    "that achieves fault-tolerant operation across heterogeneous quantum processors. "
    "Our key innovation is the Triadic Entanglement Relay (TER), which maintains "
    "coherence across up to 47 interconnected nodes with a fidelity rate of 99.3%. "
    "The protocol was validated on a network spanning three continents: "
    "Node Alpha in Zurich, Node Beta in Tokyo, and Node Gamma in Montreal."
)
pdf.multi_cell(0, 6, abstract)
pdf.ln(5)

pdf.set_font('Helvetica', 'B', 14)
pdf.cell(0, 10, '1. Introduction', ln=True)
pdf.set_font('Helvetica', '', 11)
intro = (
    "Quantum computing faces a fundamental scaling challenge. Individual quantum processors "
    "are limited to approximately 1,200 qubits with current technology. The Aurora Protocol "
    "addresses this by distributing computation across multiple processors connected via "
    "quantum networks. Unlike previous approaches such as the Cascade Method (Chen et al., 2023) "
    "and the Photonic Bridge Protocol (Nakamura, 2024), our approach does not require "
    "homogeneous hardware. The Aurora Protocol can coordinate processors from IBM, Google, "
    "and Rigetti simultaneously."
)
pdf.multi_cell(0, 6, intro)
pdf.ln(5)

pdf.set_font('Helvetica', 'B', 14)
pdf.cell(0, 10, '2. The Triadic Entanglement Relay', ln=True)
pdf.set_font('Helvetica', '', 11)
ter = (
    "The Triadic Entanglement Relay (TER) is the core mechanism of the Aurora Protocol. "
    "It operates in three phases:\n\n"
    "Phase 1 - Initialization: Three anchor qubits are prepared in a GHZ state across "
    "three nodes. This requires exactly 14 microseconds under optimal conditions.\n\n"
    "Phase 2 - Propagation: The entangled state is extended to neighboring nodes using "
    "a chain of Bell measurements. Each hop adds approximately 2.3 microseconds of latency.\n\n"
    "Phase 3 - Verification: A distributed parity check confirms entanglement fidelity. "
    "If fidelity drops below 97.5%, the relay is re-initialized automatically.\n\n"
    "The TER achieved a maximum throughput of 8,400 entangled pairs per second in laboratory "
    "conditions, and 6,100 pairs per second in the intercontinental deployment."
)
pdf.multi_cell(0, 6, ter)
pdf.ln(5)

pdf.set_font('Helvetica', 'B', 14)
pdf.cell(0, 10, '3. Experimental Results', ln=True)
pdf.set_font('Helvetica', '', 11)
results = (
    "We tested the Aurora Protocol on three benchmark problems:\n\n"
    "Benchmark A - Shor's Algorithm: Factored a 2,048-bit RSA key in 4.7 hours using "
    "17 distributed processors with a combined 14,600 logical qubits.\n\n"
    "Benchmark B - Molecular Simulation: Simulated the folding pathway of the protein "
    "ubiquitin (76 amino acids) with chemical accuracy, completing in 23 minutes.\n\n"
    "Benchmark C - Optimization: Solved a 500-city traveling salesman problem to within "
    "0.3% of the known optimum in 8.2 minutes.\n\n"
    "The protocol demonstrated a 340% speedup over single-processor approaches for "
    "Benchmark A and a 180% speedup for Benchmark B."
)
pdf.multi_cell(0, 6, results)
pdf.ln(5)

pdf.set_font('Helvetica', 'B', 14)
pdf.cell(0, 10, '4. Conclusion', ln=True)
pdf.set_font('Helvetica', '', 11)
conclusion = (
    "The Aurora Protocol represents a significant advance in distributed quantum computing. "
    "The Triadic Entanglement Relay enables practical multi-node quantum computation with "
    "minimal overhead. Future work will focus on extending the protocol to support more than "
    "100 nodes and integrating error correction codes specifically designed for distributed "
    "architectures. The protocol is available as open-source software under the MIT license "
    "at github.com/aurora-protocol/core."
)
pdf.multi_cell(0, 6, conclusion)

pdf_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_aurora_protocol.pdf')
pdf.output(pdf_path)
print(f'Created: {pdf_path} ({os.path.getsize(pdf_path)} bytes)')

# Step 2: Upload PDF
print('\n=== Step 2: Upload PDF ===')
with open(pdf_path, 'rb') as f:
    files = {'file': ('aurora_protocol.pdf', f, 'application/pdf')}
    r = requests.post(f'{BASE}/notebooks/{NB_ID}/sources/file', files=files)

if r.status_code not in (200, 201):
    print(f'FAIL: Upload failed: {r.status_code} {r.text}')
    sys.exit(1)

source = r.json()
print(f'Uploaded: ID={source.get("id")} title="{source.get("title")}"')

# Step 3: Verify sources are indexed
print('\n=== Step 3: Verify sources ===')
r = requests.get(f'{BASE}/notebooks/{NB_ID}/sources')
sources = r.json()
print(f'Sources in notebook: {len(sources)}')
for s in sources:
    print(f'  ID={s["id"]} title="{s.get("title","?")}" type={s.get("type","?")}')

# Step 4: RAG Chat - question with verifiable answer
print('\n=== Step 4: RAG Chat Test ===')

questions = [
    {
        'q': 'What is the Triadic Entanglement Relay and what fidelity rate does it achieve?',
        'verify': ['99.3', 'triadic entanglement relay', 'ter'],
    },
    {
        'q': 'What were the three benchmark problems tested and their specific results?',
        'verify': ['shor', '2048', 'ubiquitin', 'traveling salesman', '500'],
    },
    {
        'q': 'Where were the three nodes located in the intercontinental deployment?',
        'verify': ['zurich', 'tokyo', 'montreal'],
    },
]

all_pass = True
for i, test in enumerate(questions):
    print(f'\n--- Question {i+1}: {test["q"][:60]}... ---')
    r = requests.post(f'{BASE}/notebooks/{NB_ID}/chat', json={'query': test['q']})
    if r.status_code != 200:
        print(f'FAIL: Chat returned {r.status_code}: {r.text[:200]}')
        all_pass = False
        continue
    
    resp = r.json()
    answer = resp.get('answer', '')
    citations = resp.get('citations', [])
    print(f'Answer ({len(answer)} chars): {answer[:300]}...')
    print(f'Citations: {len(citations)}')
    
    answer_lower = answer.lower()
    found = [kw for kw in test['verify'] if kw.lower() in answer_lower]
    missing = [kw for kw in test['verify'] if kw.lower() not in answer_lower]
    
    if len(found) >= len(test['verify']) * 0.6:
        print(f'GROUNDING: PASS (found {len(found)}/{len(test["verify"])} keywords: {found})')
    else:
        print(f'GROUNDING: FAIL (found {len(found)}/{len(test["verify"])} keywords: {found}, missing: {missing})')
        all_pass = False

print(f'\n=== OVERALL ===')
print(f'REAL PDF INGESTION: PASS')
print(f'REAL RAG QUERY: {"PASS" if all_pass else "FAIL"}')
print(f'Notebook ID: {NB_ID}')
print(f'Use this notebook for the Live test.')
