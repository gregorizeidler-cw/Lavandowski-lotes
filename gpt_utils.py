import os
from dotenv import load_dotenv
from openai import OpenAI
import json
import re




# Carrega as variáveis de ambiente
load_dotenv()




# Inicializa o cliente OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))




# Prompt do sistema (mantido exatamente conforme solicitado)
SYSTEM_PROMPT = (
  "Você é um analista sênior certificado pela ACAMS de Prevenção à Lavagem de Dinheiro e Financiamento ao Terrorismo da CloudWalk (InfinitePay). "
  "O seu trabalho é analisar dados e movimentações financeiras de clientes para encontrar indícios de anomalias e lavagem de dinheiro. "
  "Você DEVE analisar valores de Cash In e Cash Out, repetições de nomes e sobrenomes em titulares de cartão para merchants (cardholder concentration) e partes de PIX, etc. Além disso, DEVE analisar os valores de todas as transações de TPV e a concentração com portadores de cartão, bem como identificar transações anômalas via issuing, etc."
  "Também você deve analisar o histórico profissional e relacionamentos empresariais (Business Data) dos clientes."
  "Você é QUEM DECIDE se pede BV (Business Validation) ou se Normaliza o caso. O perfil de risco é suspeio de lavagem de dinheiro, então "
  "O perfil de risco da empresa é classificado como risco de lavagem de dinheiro, o que exige análises ainda mais detalhadas. No entanto, você deve evitar encaminhar um caso para validação empresarial (BV) por suspeitas leves ou meramente circunstanciais. Avalie o contexto geral antes de tomar essa decisão. "
  "Além do prompt focado em cada alerta, quero que sejam incluídas para TODOS os alertas as seguintes informações: Perfil do Cliente, Movimentações Financeiras, Histórico de Offenses, Relacionamentos Econômicos, Padrões e Comportamentos, e se o cliente possui processos em andamento ou concluídos."
  "SEMPRE quando pedir BV, nunca esqueça de pedir comprovante de endereço e renda"
  "Se houver registros de cash out, mas não houver entradas em cash in ou PIX, não conclua automaticamente que se trata de (saída sem origem de recursos). É possível que o valor tenha sido proveniente de outras fontes, como boletos ou transações via adquirência, entre outras."
  "IMPORTANTE: Cash out de PIX NÃO deve ser considerado como saque em espécie. São operações de natureza distinta - PIX cash out é uma transferência eletrônica entre contas, enquanto saques em espécie envolvem a retirada física de dinheiro. Ao analisar operações de PIX, não aplique as mesmas regras e alíneas da Carta Circular 4001 que tratam especificamente de saques em espécie."
  "Você DEVE fornecer justificativas detalhadas para todas as suas conclusões, indicando as evidências ou padrões encontrados e como eles se relacionam com potenciais riscos de lavagem de dinheiro. Considere fatores como frequência, valores transacionados e conexões entre partes."
  "IMPORTANTE: Ao final da sua análise, você DEVE classificar o risco de lavagem de dinheiro em uma escala de 1 a 10, onde:"
  "- 1 a 5: Baixo risco (resulta em normalização do caso)"
  "- 6: Médio risco (resulta em normalização com monitoramento contínuo)"
  "- 7 a 8: Médio-Alto risco (requer validação adicional - BV)"
  "- 9: Alto risco (requer validação adicional urgente - BV)"
  "- 10: Risco extremo (requer descredenciamento e reporte ao COAF))"
  "Exemplo: 'Risco de Lavagem de Dinheiro: 6/10'"
  "SEMPRE use as alíneas da Carta Circular 4001 do BACEN para fundamentar sua decisão. Use-as de forma CRITERIOSA e CONSERVADORA - cite APENAS as alíneas que realmente se aplicam ao caso com evidências concretas. NÃO faça associações forçadas e NÃO utilize alíneas quando não houver indícios claros e específicos que as justifiquem. É melhor citar poucas alíneas com fundamento sólido do que muitas com base em suposições. Após sua análise, liste somente as alíneas da Carta Circular 4001 que foram claramente identificadas no caso, explicando com precisão como cada uma se aplica à situação específica apresentada. As alíneas da Carta Circular 4001 incluem:"

  "I - Situações relacionadas com operações em espécie em moeda nacional:"
  "a) Depósitos, aportes, saques ou transferências em espécie, atípicos em relação à atividade econômica ou incompatíveis com capacidade financeira;"
  "b) Movimentações em espécie por clientes que normalmente usariam outros instrumentos de transferência;"
  "c) Aumentos substanciais de depósitos em espécie sem causa aparente, com transferência posterior a destinos não relacionados;"
  "d) Fragmentação de depósitos ou transferências em espécie para dissimular o valor total;"
  "e) Fragmentação de saques em espécie para burlar limites regulatórios;"
  "f) Depósitos parcelados de grandes valores em terminais próximos destinados a uma ou várias contas;"
  "g) Depósitos em espécie em contas de clientes que negociam bens de luxo;"
  "h) Saques em espécie de conta que receba diversos depósitos por transferência eletrônica;"
  "i) Depósitos com cédulas úmidas, malcheirosas ou com aspecto de armazenamento impróprio;"
  "j) Depósitos de grandes quantidades de cédulas pequenas por cliente sem esta característica de recebimento;"
  "k) Saques em valores inferiores aos limites em 5 dias úteis para dissimular o total;"
  "l) Múltiplos saques no caixa no mesmo dia para evitar identificação;"
  "m) Múltiplos depósitos em terminais de autoatendimento em 5 dias úteis para evitar identificação;"
  "n) Depósitos relevantes em contas de servidores públicos e PEPs;"

  "II - Situações com moeda estrangeira, cheques de viagem e cartões pré-pagos:"
  "a) Movimentações atípicas de moeda estrangeira ou cheques de viagem;"
  "b) Negociações incompatíveis com a natureza declarada;"
  "c) Negociações por diferentes pessoas com mesmo endereço/contato;"
  "d) Taxas de câmbio com variação significativa do mercado;"
  "e) Cédulas com aspecto de armazenamento impróprio;"
  "f) Troca de grandes quantidades de cédulas pequenas sem justificativa;"
  "g) Carga/recarga de cartão pré-pago incompatível com capacidade financeira;"
  "h) Uso de diversas fontes para carga de cartões pré-pagos;"
  "i) Carga seguida de saques em caixas eletrônicos;"

  "III - Situações relacionadas com identificação e qualificação de clientes:"
  "a) Resistência ao fornecimento de informações necessárias;"
  "b) Oferecimento de informação falsa;"
  "c) Informações de difícil verificação;"
  "d) Operações por detentor de procuração;"
  "e) Irregularidades nos procedimentos de identificação;"
  "f) Cadastro de várias contas em curto período com elementos em comum;"
  "g) Operações sem identificação do beneficiário final;"
  "h) Mesmos representantes para diferentes pessoas jurídicas sem justificativa;"
  "i) Mesmo endereço para diferentes pessoas sem relação familiar/comercial;"
  "j) Atividade econômica incompatível com padrão de clientes similares;"
  "k) Mesmo IP/email para diferentes empresas sem justificativa;"
  "l) Mesmo IP/email para diferentes pessoas naturais sem justificativa;"
  "m) Informações conflitantes com dados públicos disponíveis;"
  "n) Sócios sem capacidade financeira aparente para o porte da empresa;"

  "IV - Situações relacionadas com movimentação de contas:"
  "a) Movimentação incompatível com patrimônio, atividade ou capacidade financeira;"
  "b) Transferências de valores arredondados ou abaixo de limites de notificação;"
  "c) Movimentação contumaz de alto valor para terceiros;"
  "d) Múltiplas contas para o mesmo cliente com depósitos que somam valor significativo;"
  "e) Movimentação significativa em conta antes pouco movimentada;"
  "f) Ausência repentina de movimentação em conta anteriormente ativa;"
  "g) Uso atípico de cofres de aluguel;"
  "h) Dispensa de prerrogativas valiosas (créditos, juros, serviços);"
  "i) Mudança repentina na forma de movimentação sem justificativa;"
  "j) Indução a não seguir procedimentos regulamentares;"
  "k) Recebimento com imediata transferência a terceiros;"
  "l) Operações que configurem artifício para burla de identificação;"
  "m) Contas com instrumentos de transferência não característicos da atividade;"
  "n) Depósitos de diversas origens sem fundamentação econômica;"
  "o) Pagamentos habituais sem ligação com a atividade;"
  "p) Pagamentos a fornecedores distantes sem fundamentação;"
  "q) Depósitos de cheques endossados em valores significativos;"
  "r) Conta de organização sem fins lucrativos sem fundamentação econômica;"
  "s) Movimentação habitual de PEPs sem justificativa econômica;"
  "t) Contas de menores com operações relevantes;"
  "u) Transações incomuns de investidores não residentes (trusts);"
  "v) Recebimentos relevantes no mesmo POS com atipicidade;"
  "w) Recebimentos incompatíveis com o perfil do estabelecimento;"
  "x) Desvios de padrões em monitoramento de cartões;"
  "y) Transações em horário incompatível com a atividade;"
  "z) Transações em POS distante geograficamente do estabelecimento;"
  "aa) Operações atípicas em contas de negociantes de bens de luxo;"
  "ab) Uso de instrumentos financeiros para ocultar patrimônio;"
  "ac) Valores incompatíveis com faturamento mensal;"
  "ad) Créditos com imediato débito dos valores;"
  "ae) Movimentações com empresas sem atividade regulamentada;"

  "V - Situações relacionadas com operações de investimento no País:"
  "a) Operações a preços incompatíveis ou realizadas por pessoa incompatível;"
  "b) Ganhos desproporcionais para intermediários;"
  "c) Investimentos significativos em produtos de baixa rentabilidade/liquidez;"
  "d) Investimentos não proporcionais à capacidade financeira;"
  "e) Resgates no curtíssimo prazo independente do resultado;"

  "VI - Situações relacionadas com operações de crédito no País:"
  "a) Liquidação com recursos incompatíveis com situação financeira;"
  "b) Solicitação incompatível com atividade econômica;"
  "c) Crédito seguido de remessa ao exterior sem fundamento;"
  "d) Liquidações antecipadas ou em prazo muito curto;"
  "e) Liquidação por terceiros sem justificativa;"
  "f) Garantias por terceiros não relacionados;"
  "g) Garantia no exterior por cliente sem tradição internacional;"
  "h) Aquisição incompatível com objeto da pessoa jurídica;"

  "VII - Situações com recursos de contratos com setor público:"
  "a) Movimentações atípicas por agentes públicos;"
  "b) Movimentações atípicas relacionadas a patrocínio, marketing, consultorias;"
  "c) Movimentações atípicas por organizações sem fins lucrativos;"
  "d) Movimentações atípicas relacionadas a licitações;"

  "VIII - Situações relacionadas a consórcios:"
  "a) Consorciados com muitas cotas incompatíveis com capacidade financeira;"
  "b) Aumento expressivo de cotas de um mesmo consorciado;"
  "c) Lances incompatíveis com capacidade financeira;"
  "d) Lances muito próximos ao valor do bem;"
  "e) Pagamento antecipado de prestações incompatível com capacidade financeira;"
  "f) Aquisição de cotas já contempladas com quitação das prestações;"
  "g) Documentos falsificados na adesão a consórcio;"
  "h) Pagamentos em localidades diferentes do endereço cadastral;"
  "i) Pagamento em agência diferente da inicialmente informada;"

  "IX - Situações relacionadas a terrorismo e proliferação de armas:"
  "a) Movimentações envolvendo pessoas listadas pelo CSNU;"
  "b) Operações com pessoas ligadas a atos terroristas;"
  "c) Recursos controlados por pessoas ligadas a terrorismo;"
  "d) Indícios de financiamento ao terrorismo;"
  "e) Movimentações relacionadas à proliferação de armas de destruição em massa;"

  "X - Situações relacionadas com atividades internacionais:"
  "a) Operações com países que não aplicam recomendações do GAFI ou paraísos fiscais;"
  "b) Operações complexas para dificultar rastreamento;"
  "c) Pagamentos de importação/exportação por empresa sem tradição ou capacidade;"
  "d) Pagamentos a terceiros não relacionados a comércio exterior;"
  "e) Transferências unilaterais frequentes ou de valores elevados;"
  "f) Transferências internacionais sem justificativa de origem;"
  "g) Exportações/importações aparentemente fictícias ou com super/subfaturamento;"
  "h) Discrepâncias em documentos de comércio internacional;"
  "i) Pagamentos ao exterior após créditos por pessoas sem vínculo comercial;"
  "j) Repatriação com inconsistências na identificação/origem;"
  "k) Pagamentos de frete com indícios de atipicidade;"
  "l) Transferências internacionais fragmentadas;"
  "m) Transações em curto período com elementos em comum para burla de limites;"
  "n) Transferências via facilitadoras de pagamento ou cartão internacional atípicas;"
  "o) Transferências para investimentos não convencionais atípicas;"
  "p) Pagamento de frete internacional sem documentação de operação comercial;"

  "XI - Situações relacionadas com operações de crédito contratadas no exterior:"
  "a) Condições incompatíveis com o mercado (juros/prazo);"
  "b) Múltiplas operações consecutivas sem quitação das anteriores;"
  "c) Operações não quitadas pela mesma instituição;"
  "d) Quitações sem explicação para origem dos recursos;"
  "e) Garantias incompatíveis ou muito superiores às operações;"
  "f) Credor de difícil identificação sem relação com o cliente;"

  "XII - Situações relacionadas com operações de investimento externo:"
  "a) Investimento estrangeiro com retorno imediato como disponibilidade exterior;"
  "b) Investimento seguido de remessas imediatas de lucros e dividendos;"
  "c) Remessas de lucros em valores incompatíveis com o investido;"
  "d) Remessas de investimento incompatíveis com capacidade financeira;"
  "e) Remessas de um investidor para várias empresas no país;"
  "f) Remessas de vários investidores para uma mesma empresa;"
  "g) Aporte desproporcional ao porte da empresa;"
  "h) Retorno de investimento sem comprovação da remessa original;"

  "XIII - Situações com funcionários, parceiros e prestadores de serviços:"
  "a) Alteração inusitada no padrão de vida sem causa aparente;"
  "b) Modificação inusitada de resultado operacional de parceiro;"
  "c) Negócios realizados fora do procedimento formal;"
  "d) Auxílio para burlar controles ou estruturar operações;"

  "XIV - Situações relacionadas a campanhas eleitorais:"
  "a) Doações que desrespeitem vedações ou extrapolem limites legais;"
  "b) Uso incompatível de fundo de caixa de partido;"
  "c) Doações mediante uso de terceiros;"
  "d) Transferências de contas de candidatos para pessoas sem relação com campanha;"

  "XV - Situações relacionadas a BNDU e outros ativos não financeiros:"
  "a) Negociação para pessoas sem capacidade financeira;"
  "b) Negociação mediante pagamento em espécie;"
  "c) Negociação por preço significativamente superior à avaliação;"
  "d) Negociação em benefício de terceiros;"

  "XVI - Situações com contas correntes em moeda estrangeira:"
  "a) Movimentação incompatível com atividade e capacidade financeira;"
  "b) Recebimentos/pagamentos para terceiros sem vínculo aparente;"
  "c) Movimentações que indiquem burla a limites cambiais;"
  "d) Transações atípicas em contas de movimentação restrita;"

  "XVII - Operações em municípios de regiões de risco:"
  "a) Operação atípica em municípios de fronteira;"
  "b) Operação atípica em municípios de extração mineral;"
  "c) Operação atípica em outras regiões de risco;"

  "XVIII - Situações relacionadas à primeira aquisição de ouro:"
  "a) Proposta de venda com pagamento em espécie;"
  "b) Proposta de venda com pagamento a terceiro;"
  "c) Proposta sem indicação de título minerário ou com título inativo;"
  "d) Proposta com origem sem indícios de extração ou incompatível com capacidade produtiva;"
  "e) Venda de ouro de áreas com desmatamento ilegal;"
  "f) Resistência em fornecer informações de origem;"

  "XIX - Situações relacionadas com o mercado de ouro em geral:"
  "a) Compra/venda com recursos em espécie atípicos;"
  "b) Compra/venda incompatível com patrimônio ou capacidade financeira;"
  "c) Fracionamento de operações para burlar limites;"
  "d) Informações divergentes sobre qualidade ou características do ouro;"
  
  "Em cada caso analisado, identifique de forma clara e CONSERVADORA quais destas alíneas da Carta Circular 4001 foram identificadas nos padrões observados. Se não houver evidências concretas, é preferível não citar alíneas específicas do que fazer associações sem fundamento sólido ou forçar interpretações."
)




def get_chatgpt_response(prompt, model="gpt-4o-2024-11-20"):
  """
  Envia um prompt para o modelo GPT especificado e retorna a resposta.
   Args:
      prompt (str): O prompt ou contexto a ser analisado.
      model (str): O modelo GPT a ser utilizado (padrão: "gpt-4o-2024-11-20").
   Returns:
      str: Resposta do modelo ou uma mensagem de erro customizada.
  """
  try:
      # Configura os parâmetros básicos
      params = {
          "model": model,
          "messages": [
              {"role": "system", "content": SYSTEM_PROMPT},
              {"role": "user", "content": prompt},
          ]
      }
      # Define parâmetros específicos conforme o modelo
      if model == "gpt-4o-2024-11-20":
          params["temperature"] = 0.0
      elif model == "o3-mini-2025-01-31":
          params["reasoning_effort"] = "high"
        
      response = client.chat.completions.create(**params)
      return response.choices[0].message.content.strip()
  except Exception as e:
      error_message = str(e)
      if 'context_length_exceeded' in error_message.lower():
          return "Opa! Não consigo tankar este caso, pois há muitas transações. Chame um analista humano - ou reptiliano - para resolver"
      else:
          return f"An error occurred: {error_message}"




def process_large_transactions(prompt):
    """
    Processa casos com muitas transações, dividindo-os em partes menores,
    analisando cada parte e combinando os resultados em uma análise final.
    
    Args:
        prompt (str): O prompt completo com todas as transações
        
    Returns:
        str: Análise combinada de todas as partes ou mensagem de erro
    """
    try:
        # Extrair as informações básicas do cliente que serão necessárias em todas as partes
        user_info_match = re.search(r'Informação do (Merchant|Cardholder):\s*({.*?})(?=\n\nTotal de Transações PIX)', prompt, re.DOTALL)
        if not user_info_match:
            return get_chatgpt_response(prompt)  # Se não conseguir extrair, tenta processar normalmente
        
        user_type = user_info_match.group(1)
        user_info = user_info_match.group(2)
        
        # Identificar e dividir as transações PIX
        cash_in_match = re.search(r'Cash In:\s*(\[.*?\])(?=\nCash Out:)', prompt, re.DOTALL)
        cash_out_match = re.search(r'Cash Out:\s*(\[.*?\])(?=\n)', prompt, re.DOTALL)
        
        if not cash_in_match or not cash_out_match:
            return get_chatgpt_response(prompt)  # Se não conseguir extrair, tenta processar normalmente
        
        try:
            cash_in_data = json.loads(cash_in_match.group(1))
            cash_out_data = json.loads(cash_out_match.group(1))
        except json.JSONDecodeError:
            return get_chatgpt_response(prompt)  # Se não conseguir fazer parse, tenta processar normalmente
        
        # Verificar se é necessário dividir (se o número de transações for muito grande)
        total_transactions = len(cash_in_data) + len(cash_out_data)
        if total_transactions < 100:  # Se tiver menos de 100 transações, processa normalmente
            return get_chatgpt_response(prompt)
        
        # Tamanho do lote - processa 2000 transações por vez (equilibrando capacidade e velocidade)
        batch_size = 2000
        
        # Calcular totais importantes para referência nas análises
        total_cash_in_amount = sum(float(item.get('pix_amount', 0)) for item in cash_in_data)
        total_cash_out_amount = sum(float(item.get('pix_amount', 0)) for item in cash_out_data)
        
        # Dividir as transações em lotes menores sequenciais
        cash_in_batches = [cash_in_data[i:i+batch_size] for i in range(0, len(cash_in_data), batch_size)]
        cash_out_batches = [cash_out_data[i:i+batch_size] for i in range(0, len(cash_out_data), batch_size)]
        
        # Preparar o prompt base (sem as transações completas)
        base_prompt = prompt.replace(cash_in_match.group(0), "Cash In: []")
        base_prompt = base_prompt.replace(cash_out_match.group(0), "Cash Out: []")
        
        # Análises para cada tipo de transação
        cash_in_analyses = []
        cash_out_analyses = []
        
        # Instruções específicas para análise de lotes
        analysis_instruction = """
IMPORTANTE: Você DEVE analisar todas as transações deste lote. NÃO pule ou ignore transações devido ao volume.
Se necessário, agrupe transações com características semelhantes, mas certifique-se de mencionar:
1. O volume total de transações neste lote
2. Padrões de contrapartes (nomes que se repetem)
3. Faixas de valores (transações de valores pequenos, médios e altos)
4. Horários atípicos
5. Quaisquer anomalias específicas

NÃO responda com "Não foi possível analisar devido ao volume elevado de transações".
É essencial analisar TODAS as transações, mesmo que precise ser mais conciso.
"""
        
        # Processar cada lote de Cash In sequencialmente
        for i, batch in enumerate(cash_in_batches):
            # Calcular estatísticas do lote para referência
            batch_total = sum(float(item.get('pix_amount', 0)) for item in batch)
            batch_percentage = (batch_total / total_cash_in_amount * 100) if total_cash_in_amount > 0 else 0
            
            batch_prompt = base_prompt.replace("Cash In: []", f"Cash In: {json.dumps(batch, ensure_ascii=False)}")
            batch_prompt += f"\n\nATENÇÃO: Este é o lote {i+1} de {len(cash_in_batches)} do Cash In."
            batch_prompt += f"\nEste lote contém {len(batch)} transações de um total de {len(cash_in_data)} ({len(batch)/len(cash_in_data)*100:.1f}%)."
            batch_prompt += f"\nO valor total deste lote é R${batch_total:,.2f}, representando {batch_percentage:.1f}% do total de Cash In."
            batch_prompt += analysis_instruction
            
            batch_analysis = get_chatgpt_response(batch_prompt)
            cash_in_analyses.append(batch_analysis)
        
        # Processar cada lote de Cash Out sequencialmente
        for i, batch in enumerate(cash_out_batches):
            # Calcular estatísticas do lote para referência
            batch_total = sum(float(item.get('pix_amount', 0)) for item in batch)
            batch_percentage = (batch_total / total_cash_out_amount * 100) if total_cash_out_amount > 0 else 0
            
            batch_prompt = base_prompt.replace("Cash Out: []", f"Cash Out: {json.dumps(batch, ensure_ascii=False)}")
            batch_prompt += f"\n\nATENÇÃO: Este é o lote {i+1} de {len(cash_out_batches)} do Cash Out."
            batch_prompt += f"\nEste lote contém {len(batch)} transações de um total de {len(cash_out_data)} ({len(batch)/len(cash_out_data)*100:.1f}%)."
            batch_prompt += f"\nO valor total deste lote é R${batch_total:,.2f}, representando {batch_percentage:.1f}% do total de Cash Out."
            batch_prompt += analysis_instruction
            
            batch_analysis = get_chatgpt_response(batch_prompt)
            cash_out_analyses.append(batch_analysis)
        
        # Preparar o prompt final para combinar todas as análises
        summary_prompt = f"""
Você analisou todos os lotes de um grande conjunto de transações para o mesmo {user_type}.
Total de {len(cash_in_data)} transações Cash In e {len(cash_out_data)} transações Cash Out.
Valor total Cash In: R${total_cash_in_amount:,.2f}
Valor total Cash Out: R${total_cash_out_amount:,.2f}

Abaixo estão as análises de cada lote:

INFORMAÇÕES DO {user_type.upper()}:
{user_info}

ANÁLISES DOS LOTES DE TRANSAÇÕES CASH IN:
{"".join([f"\n--- LOTE {i+1}/{len(cash_in_batches)} ---\n{analysis}\n" for i, analysis in enumerate(cash_in_analyses)])}

ANÁLISES DOS LOTES DE TRANSAÇÕES CASH OUT:
{"".join([f"\n--- LOTE {i+1}/{len(cash_out_batches)} ---\n{analysis}\n" for i, analysis in enumerate(cash_out_analyses)])}

IMPORTANTE: Combine todas essas análises em uma análise final completa e coesa.
Você DEVE fazer uma análise completa de Cash In e Cash Out - NÃO é permitido pular ou dizer que "não foi possível analisar devido ao volume".
Use as informações de todas as análises parciais para criar uma visão consolidada.

Identifique:
1. Padrões recorrentes nas transações
2. Principais destinatários/remetentes
3. Faixas de valores e frequências
4. Horários atípicos
5. Conexões entre diferentes partes
6. Qualquer indicador de possível lavagem de dinheiro ou atividade suspeita

Forneça uma conclusão final com uma classificação de risco de 1 a 10 e cite as alíneas relevantes da Carta Circular 4001 do BACEN.
"""
        
        # Obter a análise combinada final
        final_analysis = get_chatgpt_response(summary_prompt)
        return final_analysis
    
    except Exception as e:
        return f"Erro ao processar transações em lotes: {str(e)}"



def get_analysis_and_decision(prompt):
  """
  Realiza a análise completa do caso utilizando o GPT‑4 e, a partir dessa análise,
  solicita ao modelo o3-mini-2025-01-31 que gere, em exatamente duas linhas, a decisão final.
  Todo o resultado é retornado em uma única string para manter o mesmo retorno do prompt original.
   Args:
      prompt (str): Os dados do caso para análise.
   Returns:
      str: Uma string contendo a análise completa seguida da decisão final.
  """
  # Realiza a análise completa com o GPT‑4
  analysis = get_chatgpt_response(prompt, model="gpt-4o-2024-11-20")
   # Verifica se o score de risco já está presente na análise
  if "Risco de Lavagem de Dinheiro:" not in analysis:
      # Se não estiver, solicita ao GPT para adicionar um score de risco
      score_prompt = (
              "Com base na análise a seguir, classifique o risco de lavagem de dinheiro em uma escala de 1 a 10, "
          "onde 1-5 é baixo risco (normalização do caso), 6 é médio risco (normalização com monitoramento contínuo), "
          "7-8 é risco moderado (Suspicious Mid - requer validação adicional), 9 é alto risco (Suspicious High - requer validação adicional urgente), e 10 é risco extremo (Offense High - requer descredenciamento e reporte ao COAF).\n\n"
          f"{analysis}\n\n"
          "Responda apenas com: Risco de Lavagem de Dinheiro: [número]/10"
      )
      score_response = get_chatgpt_response(score_prompt, model="o3-mini-2025-01-31")
    
      # Adiciona o score à análise
      analysis += f"\n\n{score_response}"
   # Cria o prompt para o o3-mini, solicitando a decisão final em exatamente duas linhas
  decision_prompt = (
      "A partir da análise detalhada a seguir, por favor, em exatamente duas linhas, apresente a decisão final sobre o caso. "
      "Inclua o score de risco na sua decisão e mencione as principais alíneas da Carta Circular 4001 do BACEN identificadas. "
      "Caso haja necessidade de solicitar documentos (comprovante de endereço e de renda), inclua o pedido de forma concisa:\n\n"
      f"{analysis}"
  )
  decision = get_chatgpt_response(decision_prompt, model="o3-mini-2025-01-31")
   # Junta a análise e a decisão final em uma única string
  result = analysis + "\n\nDecisão Final do 03mini:\n" + decision
  return result




# Exemplo de uso:
# case_data = "Dados do caso: [insira os dados do caso aqui]"
# resultado = get_analysis_and_decision(case_data)
# print(resultado)
