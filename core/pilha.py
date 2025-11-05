from collections import defaultdict
from typing import Dict, Set, Tuple, Optional, List
import json

EPSILON = "&"

class AutomatoPilha:
    """
    Representa um Autômato de Pilha (Pushdown Automaton - PDA).
    """
    def __init__(self):
        self.states: Set[str] = set()
        self.input_alphabet: Set[str] = set()
        self.stack_alphabet: Set[str] = set()
        self.start_state: Optional[str] = None
        self.start_stack_symbol: str = 'Z'
        self.final_states: Set[str] = set()
        self.transitions: Dict[Tuple[str, str, str], Set[Tuple[str, str]]] = defaultdict(set)

    def add_state(self, state: str, is_start: bool = False, is_final: bool = False):
        self.states.add(state)
        if is_start or (self.start_state is None and len(self.states) == 1):
            self.start_state = state
        if is_final:
            self.final_states.add(state)

    def add_transition(self, src: str, input_sym: str, pop_sym: str, dst: str, push_syms: str):
        """
        Adiciona uma transição.
        - input_sym: Símbolo a ser lido da entrada (ou ε, ou multi-caractere como "aa").
        - pop_sym: Símbolo a ser desempilhado (ou ε).
        - push_syms: Símbolos a serem empilhados (ou ε). Empilha da direita para a esquerda (último caractere no topo).
        """
        if src not in self.states or dst not in self.states:
            raise ValueError("Estado de origem ou destino inválido.")

        if input_sym != EPSILON: self.input_alphabet.add(input_sym)
        if pop_sym != EPSILON: self.stack_alphabet.add(pop_sym)
        for sym in push_syms:
            if sym != EPSILON: self.stack_alphabet.add(sym)

        self.stack_alphabet.add(self.start_stack_symbol)

        self.transitions[(src, input_sym, pop_sym)].add((dst, push_syms))

    def remove_state(self, state_to_remove: str):
        """Remove um estado e todas as suas transições associadas."""
        if state_to_remove not in self.states:
            return

        self.states.discard(state_to_remove)

        if self.start_state == state_to_remove:
            self.start_state = None

        self.final_states.discard(state_to_remove)

        new_transitions = defaultdict(set)
        for (src, inp, pop), destinations in self.transitions.items():
            if src != state_to_remove:
                new_destinations = {d for d in destinations if d[0] != state_to_remove}
                if new_destinations:
                    new_transitions[(src, inp, pop)] = new_destinations
        self.transitions = new_transitions

    def rename_state(self, old_name: str, new_name: str):
        """Renomeia um estado em toda a estrutura do autômato."""
        if old_name not in self.states:
            raise ValueError(f"Estado '{old_name}' não existe.")
        if new_name in self.states and new_name != old_name:
            raise ValueError(f"O nome '{new_name}' já está em uso.")

        self.states.remove(old_name)
        self.states.add(new_name)

        if self.start_state == old_name:
            self.start_state = new_name
        
        if old_name in self.final_states:
            self.final_states.remove(old_name)
            self.final_states.add(new_name)

        new_transitions = defaultdict(set)
        for (src, inp, pop), destinations in self.transitions.items():
            new_src = new_name if src == old_name else src
            new_destinations = set()
            for dst, push in destinations:
                new_destinations.add((new_name if dst == old_name else dst, push))
            new_transitions[(new_src, inp, pop)] = new_destinations
        self.transitions = new_transitions
        
    def remove_pda_transition(self, src: str, input_sym: str, pop_sym: str, dst: str, push_syms: str):
        """Remove uma transição específica."""
        key = (src, input_sym, pop_sym)
        target = (dst, push_syms)
        if key in self.transitions:
            self.transitions[key].discard(target)
            if not self.transitions[key]:
                del self.transitions[key]


    def simulate_history(self, input_str: str) -> Tuple[List[Tuple[str, int, Tuple[str, ...]]], bool]:
        """
        Simula a execução e retorna o histórico de configurações para animação.
        Modificado para suportar transições com múltiplos caracteres (ex: "aa").

        Retorna (histórico, aceito).
        Histórico é List[Tuple[estado_representativo, input_idx_consumido, pilha_representativa]]
        """
        if not self.start_state:
            return [], False

        initial_config = (self.start_state, 0, (self.start_stack_symbol,))
    
        current_configs = self._get_epsilon_closure({initial_config})
        
        history: List[Tuple[str, int, Tuple[str, ...]]] = []
        if current_configs:
            rep_state, rep_idx, rep_stack = next(iter(current_configs))
            history.append((rep_state, rep_idx, rep_stack))
        else:
            history.append((self.start_state or "-", 0, (self.start_stack_symbol,)))

        input_idx = 0
        while input_idx < len(input_str):
            possible_symbols = {sym for (src, sym, pop) in self.transitions.keys() if sym != EPSILON}
            sorted_symbols = sorted(list(possible_symbols), key=len, reverse=True)

            consumed_symbol = None
            remaining_input = input_str[input_idx:]

            for symbol in sorted_symbols:
                if remaining_input.startswith(symbol):
                    consumed_symbol = symbol
                    break
            
            if consumed_symbol:
                next_configs_after_move = self._move_with_symbol(current_configs, consumed_symbol)
                current_configs = self._get_epsilon_closure(next_configs_after_move)
                input_idx += len(consumed_symbol)
            else:
                current_configs = set()

            if not current_configs:
                break

            rep_state, _, rep_stack = next(iter(current_configs))
            history.append((rep_state, input_idx, rep_stack))

        accepted = False
        if current_configs:
            if input_idx == len(input_str):
                accepted = any(state in self.final_states for state, _, _ in current_configs)

        return history, accepted

    def _get_epsilon_closure(self, configs: Set[Tuple[str, int, Tuple[str, ...]]]) -> Set[Tuple[str, int, Tuple[str, ...]]]:
        """Calcula o fecho-epsilon de um conjunto de configurações (estado, indice, pilha)."""
        closure = set(configs)
        queue = list(configs)

        while queue:
            state, input_idx, stack = queue.pop(0)

            key = (state, EPSILON, EPSILON)
            for next_state, push_syms in self.transitions.get(key, set()):
                new_stack = stack + tuple(push_syms) if push_syms != EPSILON else stack
                new_config = (next_state, input_idx, new_stack)
                if new_config not in closure:
                    closure.add(new_config)
                    queue.append(new_config)
            
            top = stack[-1] if stack else None
            if top:
                key = (state, EPSILON, top)
                for next_state, push_syms in self.transitions.get(key, set()):
                    stack_base = stack[:-1]
                    new_stack = stack_base + tuple(push_syms) if push_syms != EPSILON else stack_base
                    new_config = (next_state, input_idx, new_stack)
                    if new_config not in closure:
                        closure.add(new_config)
                        queue.append(new_config)
        return closure

    def _move_with_symbol(self, configs: Set[Tuple[str, int, Tuple[str, ...]]], symbol: str) -> Set[Tuple[str, int, Tuple[str, ...]]]:
        """Processa transições para um símbolo de entrada específico (pode ser multi-caractere)."""
        next_configs = set()

        for state, input_idx, stack in configs:
            key = (state, symbol, EPSILON)
            for next_state, push_syms in self.transitions.get(key, set()):
                new_stack = stack + tuple(push_syms) if push_syms != EPSILON else stack
                next_configs.add((next_state, input_idx, new_stack))

            top = stack[-1] if stack else None
            if top:
                key = (state, symbol, top)
                for next_state, push_syms in self.transitions.get(key, set()):
                    stack_base = stack[:-1]
                    new_stack = stack_base + tuple(push_syms) if push_syms != EPSILON else stack_base
                    next_configs.add((next_state, input_idx, new_stack))
        return next_configs


    def simulate(self, input_str: str) -> bool:
        """
        Simula a execução do autômato de pilha.
        Retorna True se a cadeia é aceita, False caso contrário.
        """
        if not self.start_state:
            return False

        _, accepted = self.simulate_history(input_str)
        return accepted

    def to_json(self) -> str:
        """Serializa o autômato para uma string JSON."""
        serializable_transitions = {}
        for (src, inp, pop_sym), dests in self.transitions.items():
            key = f"{src},{inp},{pop_sym}"
            serializable_transitions[key] = [list(d) for d in dests]

        input_alpha = list(filter(lambda x: isinstance(x, str), self.input_alphabet))
        stack_alpha = list(filter(lambda x: isinstance(x, str), self.stack_alphabet))


        data = {
            "states": list(self.states),
            "input_alphabet": input_alpha,
            "stack_alphabet": stack_alpha,
            "start_state": self.start_state,
            "start_stack_symbol": self.start_stack_symbol,
            "final_states": list(self.final_states),
            "transitions": serializable_transitions,
        }
        return json.dumps(data, indent=2, ensure_ascii=False)

    @classmethod
    def from_json(cls, json_str: str) -> 'AutomatoPilha':
        """Cria um Autômato de Pilha a partir de uma string JSON."""
        data = json.loads(json_str)
        pda = cls()
        pda.states = set(data.get("states", []))
        pda.input_alphabet = set(data.get("input_alphabet", []))
        pda.stack_alphabet = set(data.get("stack_alphabet", []))
        pda.start_state = data.get("start_state")
        pda.start_stack_symbol = data.get("start_stack_symbol", 'Z')
        pda.final_states = set(data.get("final_states", []))
        
        if pda.start_stack_symbol:
             pda.stack_alphabet.add(pda.start_stack_symbol)

        for key, dests in data.get("transitions", {}).items():
            try:
                parts = key.split(',', 2)
                if len(parts) == 3:
                    src, inp, pop_sym = parts
                    pda.transitions[(src, inp, pop_sym)] = {tuple(d) for d in dests}
                    if inp != EPSILON: pda.input_alphabet.add(inp)
                    if pop_sym != EPSILON: pda.stack_alphabet.add(pop_sym)
                    for _, push_list in dests:
                        for char in push_list:
                             if char != EPSILON: pda.stack_alphabet.add(char)

                else:
                    print(f"Aviso: Ignorando chave de transição malformada: {key}")
            except Exception as e:
                 print(f"Aviso: Erro ao processar transição {key} -> {dests}: {e}")

        if pda.start_state not in pda.states:
            if pda.states:
                pda.start_state = next(iter(pda.states))
                print(f"Aviso: Estado inicial '{data.get('start_state')}' não encontrado. Definindo '{pda.start_state}' como inicial.")
            else:
                 pda.start_state = None


        return pda

def snapshot_of_pda(automato: AutomatoPilha, positions: Dict[str, Tuple[int, int]]) -> str:
    """Retorna JSON serializável representando o estado completo (autômato + posições)."""
    data = {
        "automato": json.loads(automato.to_json()),
        "positions": positions
    }
    return json.dumps(data, ensure_ascii=False)

def restore_from_pda_snapshot(s: str) -> Tuple[AutomatoPilha, Dict[str, Tuple[int, int]]]:
    """Restaura um autômato de pilha e suas posições a partir de um snapshot JSON."""
    data = json.loads(s)
    
    automato_data = data.get("automato", {})
    if isinstance(automato_data, str):
        automato_data = json.loads(automato_data)

    automato = AutomatoPilha.from_json(json.dumps(automato_data))
    positions = data.get("positions", {})
    return automato, positions