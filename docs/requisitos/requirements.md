# Simulador de Cobranças por Assinatura

## Objetivo

Desenvolver um sistema de cobranças mensais por assinatura, para ter controle dos pagamentos do mês de cada cliente. Os administradores querem verificar o faturamento recorrente e qual a taxa de cobranças, para por futuramente em um dashboard.

---
## Usuarios do Sistema

- Clientes
- Administrador

## Problemas Identificados

O método de pagamento usado as vezes falha e o pagamento não é realizado, como por exemplo, um cartão sem limites como método de pagamento.

## Requisitos Funcionais

- RF01 - Cadastrar cliente 
- RF02 - Editar cliente 
- RF03 - Desativar cliente 
- RF04 - Cadastrar planos 
- RF05 - Registrar pagamentos 
- RF06 - Consultar clientes 
- RF07 - Gerenciar faturamentos
- RF08 - Emitir relatórios
- RF09 - Exibir as taxas de cobrança 
- RF10 - Fazer assinatura para o usuário 
- RF11 - Cancelar assinatura 
- RF12 - Atualizar planos 
- RF13 - Atualizar assinatura 

## Requisitos Não Funcionais

- RNF01 - O sistema deve possuir autenticação. 
- RNF02 - O pagamento vencido bloqueia o funcionamento do plano.
- RNF03 - Apenas administradores tem acesso ao faturamento.
- RNF04 - Apenas adminitradores podem desativar clientes. 
- RNF05 - Apenas uma assinatura por cliente. 

## Dúvidas para o Cliente

- Existe integração com maquininhas de pagamento?
- O próprio aluno pode mudar o plano dele de Básico para Premium, por exemplo?
- O cancelamento da assinatura pode ser feita pelo cliente também?
- A empresa tem recepcionistas, faturistas e administradores, ou todos da empresa poderão ter acesso as dados dos clientes?
- Haverá emissões de recibos?