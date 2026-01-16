#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for detailed diagram generation
Tests the enhanced diagram exporter with the example JSON data
"""

import json
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.analyzers import extract_detailed_flow, _extract_transitions
from utils.diagram_exporter import export_detailed_flow_diagram, export_intent_flow_diagram


def test_transition_extraction():
    """Test that transitions are correctly extracted from the example data."""
    print("=" * 80)
    print("🧪 TEST 1: Transition Extraction")
    print("=" * 80)
    
    with open('test_intent_example.json', 'r', encoding='utf-8') as f:
        intents = json.load(f)
    
    intent = intents[0]
    transitions = _extract_transitions(intent)
    
    print(f"\n📊 Found {len(transitions)} transitions:")
    for t in transitions:
        condition = f" [{t.condition}]" if t.condition else ""
        print(f"   {t.transition_type}: {t.source_id[:20]}... -> {t.target_id}{condition}")
    
    # Verify we found the expected transitions
    expected_targets = [
        'ccConsultationAutoOsagoChange',
        'ccOTMKASKOAQF', 
        'ccMortgageChanges',
        'ccIFLChangePolis',
        'cc_travel_change_1',
        'kc_Gen_Int_NeedChange_DMS',
        'ccNeedChangeOther',
        'ccPolicyChangeAndProlong'
    ]
    
    found_targets = {t.target_id for t in transitions}
    missing = set(expected_targets) - found_targets
    
    if missing:
        print(f"\n⚠️  Missing targets: {missing}")
    else:
        print(f"\n✅ All expected targets found!")
    
    return len(transitions) > 0


def test_detailed_flow_extraction():
    """Test detailed flow extraction."""
    print("\n" + "=" * 80)
    print("🧪 TEST 2: Detailed Flow Extraction")
    print("=" * 80)
    
    with open('test_intent_example.json', 'r', encoding='utf-8') as f:
        intents = json.load(f)
    
    intent = intents[0]
    flow = extract_detailed_flow(intent)
    
    print(f"\n📋 Intent: {flow['intent_id'][:40]}...")
    print(f"   Title: {flow['title'][:50]}...")
    print(f"   Record type: {flow['record_type']}")
    
    print(f"\n📝 Entry conditions: {len(flow['entry_conditions'])}")
    for cond in flow['entry_conditions']:
        pattern = cond['pattern'][:60] + "..." if len(cond['pattern']) > 60 else cond['pattern']
        print(f"   - {cond['type']}: {pattern}")
    
    print(f"\n🔀 Branches: {len(flow['branches'])}")
    for idx, branch in enumerate(flow['branches']):
        slots = branch.get('slot_conditions', [])
        redirects = branch.get('redirects', [])
        buttons = branch.get('buttons', [])
        actions = branch.get('actions', [])
        
        print(f"\n   Branch {idx + 1}:")
        if slots:
            print(f"      Slot conditions: {len(slots)}")
            for s in slots[:2]:
                print(f"         - {s['slot_id']} = {s['values']}")
        if redirects:
            print(f"      Redirects: {redirects}")
        if buttons:
            print(f"      Buttons: {len(buttons)}")
            for b in buttons[:3]:
                print(f"         - [{b.get('text', '?')}] -> {b.get('action_id', '?')}")
        if actions:
            print(f"      Actions: {len(actions)}")
            for a in actions[:2]:
                print(f"         - {a['type']}: {a.get('slot', '')} {a.get('value', '')}")
    
    print(f"\n🔗 Total transitions: {len(flow['transitions'])}")
    
    return len(flow['branches']) > 0


def test_diagram_generation():
    """Test diagram file generation."""
    print("\n" + "=" * 80)
    print("🧪 TEST 3: Diagram Generation")
    print("=" * 80)
    
    with open('test_intent_example.json', 'r', encoding='utf-8') as f:
        intents = json.load(f)
    
    # Create output directory
    os.makedirs('test_output', exist_ok=True)
    
    # Test 1: Detailed flow diagram for all intents
    print("\n📊 Generating detailed flow diagram...")
    export_detailed_flow_diagram(
        intents=intents,
        output_path='test_output/detailed_flow.mmd',
        show_slot_conditions=True,
        show_buttons=True,
        show_regex=True
    )
    
    # Test 2: Single intent flow diagram
    print("\n📊 Generating single intent diagram...")
    export_intent_flow_diagram(
        intent=intents[0],
        output_path='test_output/intent_flow.mmd'
    )
    
    # Read and display the generated diagrams
    print("\n" + "=" * 80)
    print("📄 Generated Diagram Content (detailed_flow.mmd):")
    print("=" * 80)
    
    with open('test_output/detailed_flow.mmd', 'r', encoding='utf-8') as f:
        content = f.read()
        print(content)
    
    print("\n" + "=" * 80)
    print("📄 Generated Diagram Content (intent_flow.mmd):")
    print("=" * 80)
    
    with open('test_output/intent_flow.mmd', 'r', encoding='utf-8') as f:
        content = f.read()
        print(content)
    
    return os.path.exists('test_output/detailed_flow.mmd') and os.path.exists('test_output/intent_flow.mmd')


def test_nan_handling():
    """Test that NaN values in record_type and other fields are handled correctly."""
    print("\n" + "=" * 80)
    print("🧪 TEST 4: NaN/Float Handling")
    print("=" * 80)
    
    # Create test data with NaN values
    test_intents = [
        {
            "intent_id": "test-nan-1",
            "title": "Test with NaN",
            "record_type": float('nan'),  # NaN value
            "answers": [{"answer": "Hello"}],
            "inputs": []
        },
        {
            "intent_id": "test-nan-2", 
            "title": float('nan'),  # NaN title
            "record_type": "cc_match",
            "answers": [],
            "inputs": []
        },
        {
            "intent_id": float('nan'),  # NaN intent_id
            "title": "Test",
            "record_type": None,  # None value
            "answers": [],
            "inputs": []
        }
    ]
    
    os.makedirs('test_output', exist_ok=True)
    
    try:
        # Test detailed flow diagram
        print("\n📊 Testing detailed flow diagram with NaN values...")
        export_detailed_flow_diagram(
            intents=test_intents,
            output_path='test_output/nan_test.mmd',
            show_slot_conditions=True,
            show_buttons=True,
            show_regex=True
        )
        print("✅ Detailed flow diagram generated successfully")
        
        # Verify file was created
        if os.path.exists('test_output/nan_test.mmd'):
            with open('test_output/nan_test.mmd', 'r') as f:
                content = f.read()
                print(f"✅ File created with {len(content)} characters")
            return True
        else:
            print("❌ File was not created")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("🚀 DIAGRAM GENERATION TEST SUITE")
    print("=" * 80)
    
    tests = [
        ("Transition Extraction", test_transition_extraction),
        ("Detailed Flow Extraction", test_detailed_flow_extraction),
        ("Diagram Generation", test_diagram_generation),
        ("NaN/Float Handling", test_nan_handling),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed, None))
        except Exception as e:
            results.append((name, False, str(e)))
            import traceback
            traceback.print_exc()
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 TEST SUMMARY")
    print("=" * 80)
    
    for name, passed, error in results:
        status = "✅ PASSED" if passed else f"❌ FAILED"
        if error:
            status += f" ({error})"
        print(f"   {name}: {status}")
    
    all_passed = all(r[1] for r in results)
    print("\n" + ("✅ All tests passed!" if all_passed else "❌ Some tests failed"))
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
