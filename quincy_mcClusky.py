from itertools import product
import json

def is_pos_expression(expr):
    return '(' in expr and ')' in expr and '*' not in expr

def pos_to_sop(pos_input):
    product_terms = pos_input.replace(" ", "").split(')(')
    product_terms = [term.strip('()') for term in product_terms]
    sum_terms = [term.split('+') for term in product_terms]
    
    sop_terms = []
    current_terms = sum_terms[0]
    
    for next_terms in sum_terms[1:]:
        new_terms = []
        for term1 in current_terms:
            for term2 in next_terms:
                combined = term1 + term2
                seen = {}
                valid = True
                for i in range(0, len(combined)):
                    if combined[i].isalpha():
                        var = combined[i]
                        negated = (i+1 < len(combined)) and (combined[i+1] == "'")
                        literal = var + "'" if negated else var
                        if var in seen:
                            if seen[var] != literal:
                                valid = False
                                break
                        else:
                            seen[var] = literal
                if valid:
                    unique_literals = sorted(list(seen.values()), key=lambda x: x[0])
                    new_term = ''.join(unique_literals)
                    if new_term not in new_terms:
                        new_terms.append(new_term)
        current_terms = new_terms
        if not current_terms:
            break
    
    return current_terms

def expand_terms(sop_terms):
    all_vars = set()
    for term in sop_terms:
        all_vars.update(char for char in term if char.isalpha())
    all_vars = sorted(all_vars)

    expanded_minterms = []
    for term in sop_terms:
        present_vars = set(char for char in term if char.isalpha())
        missing_vars = sorted(set(all_vars) - present_vars)
        placeholders = list(product("01", repeat=len(missing_vars)))

        for combo in placeholders:
            complete_term = term
            for mv, val in zip(missing_vars, combo):
                complete_term += mv if val == '1' else mv + "'"
            sorted_term = ''.join(sorted(
                [complete_term[i:i+2] if i+1 < len(complete_term) and complete_term[i+1] == "'" else complete_term[i]
                for i in range(len(complete_term)) if complete_term[i].isalpha()],
                key=lambda x: x[0]
            ))
            expanded_minterms.append(sorted_term)

    return expanded_minterms, all_vars, None

def sop_to_minterms(expanded_terms, num_vars, all_vars):
    term_map = {}
    for i in range(2 ** num_vars):
        bin_repr = bin(i)[2:].zfill(num_vars)
        expr = ''
        for idx, val in enumerate(bin_repr):
            expr += all_vars[idx] + ("'" if val == '0' else "")
        term_map[expr] = i

    minterms = []
    for term in expanded_terms:
        if term in term_map:
            minterms.append(term_map[term])
        else:
            return None, f"Invalid or mistyped term: {term}"

    return minterms, None

def validate_input(values, label, num_vars):
    max_value = (2 ** num_vars) - 1
    if any(v > max_value for v in values):
        return False, f"This is a {num_vars}-bit solver and does not support {label} greater than {max_value}."
    return True, None

def findVariables(binary_str, all_vars):
    var_list = []
    for i in range(len(binary_str)):
        if binary_str[i] == '0':
            var_list.append(all_vars[i] + "'")
        elif binary_str[i] == '1':
            var_list.append(all_vars[i])
    return var_list

def simplify_sop(sop_input):
    try:
        if is_pos_expression(sop_input):
            sop_terms = pos_to_sop(sop_input)
            if not sop_terms:
                return {"success": False, "error": "POS expression simplifies to 0 (contradiction)"}
            sop_input = '+'.join(sop_terms)
        
        sop_terms = sop_input.replace(" ", "").split('+')
        if not sop_terms or any(not term for term in sop_terms):
            return {"success": False, "error": "Invalid expression. Please provide terms separated by '+'."}

        expanded_terms, all_vars, error = expand_terms(sop_terms)
        if error:
            return {"success": False, "error": error}

        num_vars = len(all_vars)
        if(num_vars > 5):
            return {"success": False, "error": "This is a 5-bit solver and does not support more than 5 variables."}

        minterms, error = sop_to_minterms(expanded_terms, num_vars, all_vars)
        if error:
            return {"success": False, "error": error}

        valid, error = validate_input(minterms, "minterms", num_vars)
        if not valid:
            return {"success": False, "error": error}

        minterms.sort()
        groups = {}
        binary_input = []
        for minterm in minterms:
            bit_count = bin(minterm).count('1')
            binary = bin(minterm)[2:].zfill(num_vars)
            groups.setdefault(bit_count, []).append(binary)
            binary_input.append(binary)

        all_pi = set()
        while True:
            tmp = groups.copy()
            groups, marked, should_stop = {}, set(), True
            l = sorted(tmp.keys())
            for i in range(len(l) - 1):
                for j in tmp[l[i]]:
                    for k in tmp[l[i + 1]]:
                        diff = [x != y for x, y in zip(j, k)]
                        if sum(diff) == 1:
                            should_stop = False
                            index = diff.index(True)
                            merged = j[:index] + '-' + j[index + 1:]
                            groups.setdefault(l[i], []).append(merged)
                            marked.update([j, k])
            all_pi.update(set(sum(tmp.values(), [])) - marked)
            if should_stop:
                break

        prime_implicants = ', '.join(sorted(all_pi))
        solution = ' + '.join(''.join(findVariables(i, all_vars)) for i in sorted(all_pi))
        result_text = f"Essential Prime Implicants: {prime_implicants}\nSimplified Expression: F = {solution}"
        return {
            "success": True,
            "binaryInput": ', '.join(binary_input),
            "result": result_text
        }

    except Exception as e:
        return {"success": False, "error": f"An unexpected error occurred: {str(e)}"}
