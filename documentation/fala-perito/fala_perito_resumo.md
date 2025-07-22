# Fala, Perito! - Visão Geral

## Introdução

O "Fala, Perito!" é um assistente de chat integrado ao IPED (Indexador e Processador de Evidências Digitais) que utiliza inteligência artificial para auxiliar peritos na análise de evidências digitais. Este documento apresenta uma visão geral das funcionalidades implementadas e as principais classes modificadas.

## Funcionalidades Principais

### 1. Interface de Chat Interativa

- **Painel de Chat Dedicado**: Interface amigável integrada ao IPED como um componente dockable
- **Mensagens Estilizadas**: Diferenciação visual entre mensagens do usuário e do assistente
- **Indicador de Digitação**: Feedback visual enquanto o assistente processa a resposta
- **Entrada de Texto Multi-linha**: Suporte a mensagens longas com quebras de linha

### 2. Contextualização com Evidências

- **Adição de Chats ao Contexto**: Possibilidade de adicionar conversas específicas como contexto para as perguntas
- **Gerenciamento Visual de Contexto**: Interface para adicionar e remover chats do contexto atual
- **Identificação por Cores**: Sistema de cores para identificar diferentes chats no contexto

### 3. Processamento Inteligente de Contexto

- **Análise de Conversas**: Capacidade de processar e entender o conteúdo de conversas de WhatsApp
- **Resumos Automáticos**: Geração e utilização de resumos de conversas longas
- **Processamento Adaptativo**: Envio de conteúdo completo ou resumido dependendo do volume de dados

### 4. Integração com API de IA

- **Comunicação Assíncrona**: Processamento em segundo plano sem bloquear a interface
- **Tratamento de Erros**: Mecanismos para lidar com falhas de comunicação ou processamento
- **Formatação de Respostas**: Apresentação clara e estruturada das respostas do assistente

## Principais Classes Modificadas

### 1. `App.java`

Classe central da aplicação IPED que recebeu as principais modificações para implementar o chat:

#### Novos Atributos
```java
private DefaultSingleCDockable chatDock;
private JPanel chatPanel;
private JPanel messagesPanel;
private JTextArea inputArea;
private JLabel loadingLabel;
private Timer loadingTimer;
private List<ChatMessage> chatMessages;
private List<String> chatNames;
private List<Color> chatColors;
private List<IItem> contextChatItems;
```

#### Novos Métodos
- `createLoadingIndicator()`: Cria o indicador de "digitação" do assistente
- `showLoading()` / `hideLoading()`: Controla a visibilidade do indicador
- `addUserMessage(String text)`: Adiciona mensagem do usuário e inicia processamento
- `updateChatText(String newText)`: Atualiza o chat com a resposta do assistente
- `refreshChat()`: Renderiza todas as mensagens na interface
- `getContextChatNames()` / `getContextChatItems()`: Gerencia o contexto atual
- `addChatName(String name)` / `removeChatName(String name)`: Manipula chats no contexto
- `updateChatNamesPanel()`: Atualiza a interface com os chats em contexto

#### Classe Interna
- `ChatMessage`: Representa uma mensagem no chat com atributos para texto e origem (usuário ou assistente)

### 2. `ResultTableListener.java`

Classe responsável pela comunicação com a API de IA e processamento de contexto:

#### Novos Atributos
```java
private static final String API_URL = "http://127.0.0.1:8000/api/chat";
private static final ObjectMapper objectMapper = new ObjectMapper();
private static final Executor executor = Executors.newSingleThreadExecutor();
```

#### Novos Métodos
- `sendToOpenAI(String chatContent, String userQuestion)`: Envia perguntas e contexto para a API
- `getAllChatSummaries()`: Obtém resumos de todos os chats disponíveis
- `getContextChatSummaries(List<String> contextChatNames)`: Obtém resumos dos chats em contexto
- `stripHtmlTags(String html)`: Limpa conteúdo HTML para processamento

## Fluxo de Funcionamento

1. **Inicialização**: O chat é carregado com uma mensagem de boas-vindas
2. **Entrada do Usuário**: O usuário digita uma pergunta e pressiona Enter
3. **Processamento**:
   - A mensagem é exibida no chat
   - O indicador de carregamento é ativado
   - O contexto relevante é coletado (conversas completas ou resumos)
   - A pergunta e o contexto são enviados para a API
4. **Resposta**:
   - A resposta da API é recebida
   - O indicador de carregamento é desativado
   - A resposta é exibida no chat

## Integração com o IPED

O "Fala, Perito!" se integra perfeitamente à interface do IPED através do sistema de docking, permitindo que os peritos utilizem o assistente enquanto analisam evidências. A implementação aproveita a infraestrutura existente do IPED para acessar e processar os dados das evidências digitais, especialmente conversas de WhatsApp.

## Considerações Técnicas

- **Processamento Assíncrono**: Utilização de executores para evitar bloqueio da interface
- **Tratamento de Erros**: Captura e log de exceções durante a comunicação com a API
- **Otimização de Dados**: Envio seletivo de conteúdo completo ou resumido conforme necessário
- **Interface Responsiva**: Atualização dinâmica da interface usando SwingUtilities.invokeLater

## Conclusão

O "Fala, Perito!" representa uma evolução significativa na interface do IPED, adicionando capacidades de assistência baseada em IA que podem acelerar e melhorar o trabalho dos peritos. A implementação foi cuidadosamente integrada à arquitetura existente do IPED, mantendo a coesão do sistema enquanto adiciona novas funcionalidades poderosas.
