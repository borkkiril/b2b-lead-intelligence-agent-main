import sqlite3
import re

conn = sqlite3.connect('data/leads.db')
c = conn.cursor()
c.execute('SELECT id, inbox_slot, company, website, contact_role, verified_email, email_step1_plain_text, email_step1_5_followup, notion_adaptation_blueprint FROM leads')
rows = c.fetchall()

print(f"Total leads in DB: {len(rows)}")
inbox_counts = {}
for r in rows:
    lid, slot, comp, web, role, email, email1, follow, blueprint = r
    inbox_counts[slot] = inbox_counts.get(slot, 0) + 1
    
    # 1. Check no links in email1
    assert 'http://' not in email1 and 'https://' not in email1, f"Link found in email1 for {comp}"
    words = len(email1.split())
    
    # 2. Check follow-up formula
    assert 'Staging Sandbox' in follow, f"Staging sandbox missing in follow for {comp}"
    assert '0% risk of breaking production ERP' in follow, f"0% risk missing in follow for {comp}"
    assert '$20,000' in follow, f"20k missing in follow for {comp}"
    assert 'Happy to answer any questions you may have.' in follow, f"Ending phrase missing in follow for {comp}"
    
    # 3. Check blueprint
    assert 'Stripe Checkout' in blueprint, f"Stripe missing in blueprint for {comp}"
    assert 'VAT Reverse Charge' in blueprint, f"SEPA missing in blueprint for {comp}"
    
    # Extract code lines
    code_match = re.search(r'```python\n(.*?)```', blueprint, re.DOTALL)
    assert code_match, f"Code block missing in blueprint for {comp}"
    code_text = code_match.group(1).strip()
    code_lines = [l for l in code_text.splitlines()]
    
    print(f"[{lid:02d}] {slot:<8} | {comp:<16} | Words: {words:<3} | Code lines: {len(code_lines):<2} | OK")

print("\nInbox distribution:", inbox_counts)
conn.close()
