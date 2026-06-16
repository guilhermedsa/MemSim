###
###     S I M U L A D O R    D E    M E M Ó R I A
###
### Prof. Filipo - github.com/ProfessorFilipo/MemSim/
### Adaptado para o Grupo 12: Ótimo (OPT) vs Segunda Chance (Clock)
###

import sys

class Frame:
    def __init__(self, id_frame):
        self.id_frame = id_frame
        self.pagina_alocada = None  # Armazena o número da página ou None se estiver vazio
        # Atributo adicionado para a lógica do algoritmo Segunda Chance (Clock)
        self.bit_referencia = 0  


class TabelaPaginas:
    def __init__(self, num_frames, algoritmo, sequencia_acessos):
        # Inicializa a memória física com a quantidade de frames especificada
        self.frames = [Frame(i) for i in range(num_frames)]
        self.total_page_faults = 0
        self.total_acessos = 0
        
        # Variáveis de controle para os algoritmos
        self.algoritmo = algoritmo.upper()
        self.sequencia_acessos = sequencia_acessos
        self.passo_atual = 0
        self.ponteiro_clock = 0  # Ponteiro circular para o algoritmo Clock

    def acessar_pagina(self, numero_pagina):
        self.total_acessos += 1

        # 1. Verificar se a página já está em algum frame (Hit)
        for frame in self.frames:
            if frame.pagina_alocada == numero_pagina:
                # Atualização de metadados para o CLOCK (Bit de referência = 1)
                if self.algoritmo == "CLOCK":
                    frame.bit_referencia = 1
                
                self.passo_atual += 1
                return True, frame.id_frame  # Retorna (Hit=True, frame_id)

        # 2. Se não encontrou, ocorreu um Page Fault!
        self.total_page_faults += 1

        # 3. Verificar se existe algum frame vazio disponível
        for frame in self.frames:
            if frame.pagina_alocada is None:
                frame.pagina_alocada = numero_pagina
                
                # Inicialização de metadados para o CLOCK ao usar frame vazio
                if self.algoritmo == "CLOCK":
                    frame.bit_referencia = 1
                    # Avança o ponteiro circular
                    self.ponteiro_clock = (self.ponteiro_clock + 1) % len(self.frames)
                
                self.passo_atual += 1
                return False, frame.id_frame  # Retorna (Hit=False, frame_id)

        # 4. Memória cheia: Aplicar algoritmo de substituição de página
        frame_vitima_id = self.substituir_pagina(numero_pagina)
        self.passo_atual += 1
        return False, frame_vitima_id

    def substituir_pagina(self, nova_pagina):
        """
        Lógica dos Algoritmos ÓTIMO (OPT) e SEGUNDA CHANCE (CLOCK) - Grupo 12
        """
        frame_escolhido_id = 0

        if self.algoritmo == "OPT":
            # Look-ahead: analisa o fluxo de páginas futuras a partir do próximo passo
            futuro = self.sequencia_acessos[self.passo_atual:]
            maior_distancia = -1

            for frame in self.frames:
                # Se a página do frame não for mais usada no futuro, ela é a vítima ideal
                if frame.pagina_alocada not in futuro:
                    frame_escolhido_id = frame.id_frame
                    break
                else:
                    # Caso contrário, calcula qual frame demorará mais para ser usado
                    distancia = futuro.index(frame.pagina_alocada)
                    if distancia > maior_distancia:
                        maior_distancia = distancia
                        frame_escolhido_id = frame.id_frame
            
            # Executa a substituição
            self.frames[frame_escolhido_id].pagina_alocada = nova_pagina
            return frame_escolhido_id

        elif self.algoritmo == "CLOCK":
            while True:
                frame_atual = self.frames[self.ponteiro_clock]
                
                # Se o bit de referência for 0, encontramos a vítima
                if frame_atual.bit_referencia == 0:
                    frame_escolhido_id = self.ponteiro_clock
                    
                    # Substitui a página e seta o bit como 1 (nova entrada)
                    frame_atual.pagina_alocada = nova_pagina
                    frame_atual.bit_referencia = 1
                    
                    # Avança o ponteiro circular e encerra a busca
                    self.ponteiro_clock = (self.ponteiro_clock + 1) % len(self.frames)
                    return frame_escolhido_id
                else:
                    # Dá a "segunda chance": zera o bit e avança o ponteiro circular
                    frame_atual.bit_referencia = 0
                    self.ponteiro_clock = (self.ponteiro_clock + 1) % len(self.frames)

    def imprimir_mapa_memoria(self, passo, pagina_acessada, foi_hit, frame_alterado=None):
        """
        Impressão formatada exatamente conforme o gabarito do professor.
        """
        status = "Hit" if foi_hit else "Page Fault"
        print(f"--- Passo {passo}: Acesso à Página {pagina_acessada} ({status}) ---")

        for frame in self.frames:
            conteudo = f"Página {frame.pagina_alocada}" if frame.pagina_alocada is not None else "[Vazio]"
            marcador = " <-- Alterado" if frame.id_frame == frame_alterado and not foi_hit else ""
            print(f"[Frame {frame.id_frame}]: {conteudo}{marcador}")


class Simulador:
    def __init__(self, caminho_arquivo, algoritmo="OPT"):
        self.caminho_arquivo = caminho_arquivo
        self.algoritmo = algoritmo

    def executar(self):
        try:
            with open(self.caminho_arquivo, 'r') as arquivo:
                linhas = arquivo.readlines()
        except FileNotFoundError:
            print(f"Erro: O arquivo '{self.caminho_arquivo}' não foi encontrado.")
            return

        # Limpa linhas vazias ou comentários se houver
        linhas = [l.strip() for l in linhas if l.strip() and not l.strip().startswith('#')]

        if not linhas:
            print("Erro: Arquivo de entrada vazio.")
            return

        # A primeira linha válida define o número de frames na memória RAM simulada
        num_frames = int(linhas[0])
        
        # Isola apenas a sequência de acessos para uso do algoritmo OPT
        sequencia_acessos = [int(linha) for linha in linhas[1:]]

        # Inicializa a tabela de páginas repassando a sequência completa
        tabela_paginas = TabelaPaginas(num_frames, self.algoritmo, sequencia_acessos)

        print(f"Iniciando simulação com {num_frames} frames disponíveis utilizando {self.algoritmo}.")
        print("=" * 40)

        # As linhas seguintes são a sequência de acessos às páginas
        passo = 1
        for numero_pagina in sequencia_acessos:
            # Processa o acesso na tabela de páginas
            foi_hit, frame_id = tabela_paginas.acessar_pagina(numero_pagina)

            # Renderiza o mapa de memória para o aluno ver o passo a passo
            tabela_paginas.imprimir_mapa_memoria(passo, numero_pagina, foi_hit, frame_id)
            passo += 1

        # Exibição das estatísticas finais da simulação
        print("================ STATS FINAIS ================")
        print(f"Total de Acessos: {tabela_paginas.total_acessos}")
        print(f"Total de Page Faults: {tabela_paginas.total_page_faults}")
        if tabela_paginas.total_acessos > 0:
            taxa_faults = (tabela_paginas.total_page_faults / tabela_paginas.total_acessos) * 100
            print(f"Taxa de Page Faults: {taxa_faults:.2f}%")
        print("==============================================")


if __name__ == "__main__":
    # Permite passar o arquivo de entrada por argumento de linha de comando ou usa um padrão
    arquivo_entrada = sys.argv[1] if len(sys.argv) > 1 else "entrada.txt"
    
    print("\n" + "#"*50)
    print("           RODANDO ALGORITMO: ÓTIMO (OPT)         ")
    print("#"*50 + "\n")
    simulador_opt = Simulador(arquivo_entrada, algoritmo="OPT")
    simulador_opt.executar()

    print("\n\n" + "#"*50)
    print("      RODANDO ALGORITMO: SEGUNDA CHANCE (CLOCK)   ")
    print("#"*50 + "\n")
    simulador_clock = Simulador(arquivo_entrada, algoritmo="CLOCK")
    simulador_clock.executar()