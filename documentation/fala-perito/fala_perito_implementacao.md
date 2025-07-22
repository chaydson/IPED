# Documentação do Chat "Fala, Perito!" - IPED

## Visão Geral

O "Fala, Perito!" é um componente de chat integrado ao IPED (Indexador e Processador de Evidências Digitais) que permite aos usuários interagir com um assistente baseado em IA para obter ajuda e informações relacionadas às evidências digitais. O chat utiliza modelos de linguagem para processar e responder às perguntas dos usuários, considerando o contexto das conversas de WhatsApp e outras evidências presentes no caso.

## Estrutura de Classes e Componentes

### Classe Principal: `App.java`

A classe `App` é o componente central da interface do IPED e contém a implementação do chat "Fala, Perito!". Ela gerencia a interface gráfica, o processamento de mensagens e a comunicação com a API de IA.

#### Atributos Principais do Chat

```java
// Componentes da interface do chat
private DefaultSingleCDockable chatDock;
private JPanel chatPanel;
private JPanel messagesPanel;
private JTextArea inputArea;
private JButton sendButton;
private JLabel chatLabel;
private JLabel loadingLabel;
private Timer loadingTimer;
private int loadingDots = 0;
private Executor executor = Executors.newSingleThreadExecutor();

// Armazenamento de mensagens e contexto
private List<ChatMessage> chatMessages = new LinkedList<>();
private String currentChatText = "";
private List<String> chatNames = new LinkedList<>();
private List<Color> chatColors = new LinkedList<>();
private List<IItem> contextChatItems = new ArrayList<>();
```

#### Classe Interna: `ChatMessage`

Uma classe interna que representa uma mensagem no chat:

```java
private static class ChatMessage {
    String text;
    boolean isUser;
    ChatMessage(String text, boolean isUser) {
        this.text = text;
        this.isUser = isUser;
    }
}
```

### Inicialização do Chat

O chat é inicializado durante a criação da interface gráfica do IPED. Os principais passos são:

1. Criação dos componentes da interface (painel, área de mensagens, área de entrada)
2. Configuração do layout e estilo visual
3. Adição de listeners para interação do usuário
4. Criação do componente dockable para integração na interface principal

```java
// Inicialização do painel do chat
chatPanel = new JPanel(new BorderLayout());
messagesPanel = new JPanel();
messagesPanel.setLayout(new GridBagLayout());

// Configuração da área de entrada
inputArea = new JTextArea(3, 40);
inputArea.setLineWrap(true);
inputArea.setWrapStyleWord(true);

// Adiciona listener para capturar tecla Enter
inputArea.addKeyListener(new KeyAdapter() {
    @Override
    public void keyPressed(KeyEvent e) {
        if (e.getKeyCode() == KeyEvent.VK_ENTER) {
            if (e.isShiftDown()) {
                inputArea.append("\n");
            } else {
                e.consume();
                String text = inputArea.getText().trim();
                if (!text.isEmpty()) {
                    addUserMessage(text);
                    inputArea.setText("");
                }
            }
        }
    }
});

// Criação do componente dockable
chatDock = createDockable("chat", "Fala, Perito!", chatPanel);
dockingControl.addDockable(chatDock);
chatDock.setLocation(CLocation.base().normalNorth(0.1));
chatDock.setVisible(true);
```

### Métodos Principais do Chat

#### `addUserMessage(String text)`

Adiciona uma mensagem do usuário ao chat e envia para processamento pela API:

```java
private void addUserMessage(String text) {
    if (chatPanel != null && inputArea != null && messagesPanel != null) {
        chatMessages.add(new ChatMessage(text, true)); // true = usuário
        SwingUtilities.invokeLater(this::refreshChat);
        
        // Show loading indicator
        showLoading();
        
        // Get the list of chats in context
        List<String> contextChats = getContextChatNames();
        
        // Send to API with the appropriate context
        executor.execute(() -> {
            if (contextChats.isEmpty()) {
                // If no chats in context, send summaries of all chats
                ResultTableListener.sendToOpenAI("", text);
            } else if (contextChats.size() == 1) {
                // If only one chat in context, send its content
                ResultTableListener.sendToOpenAI(currentChatText, text);
            } else {
                // If multiple chats in context, send their summaries
                ResultTableListener.sendToOpenAI("", text);
            }
        });
    }
}
```

#### `updateChatText(String newText)`

Atualiza o chat com a resposta recebida da API:

```java
public void updateChatText(String newText) {
    if (chatLabel != null) {
        chatLabel.setText(newText);
    }
    // Adiciona resposta da API ao chat
    if (chatPanel != null && inputArea != null && messagesPanel != null) {
        // Hide loading indicator before adding the response
        hideLoading();
        chatMessages.add(new ChatMessage(newText, false)); // false = bot
        SwingUtilities.invokeLater(this::refreshChat);
    }
}
```

#### `refreshChat()`

Atualiza a interface do chat, renderizando todas as mensagens:

```java
private void refreshChat() {
    if (messagesPanel == null) return;
    
    // Preserva o painel de nomes dos chats
    JPanel namesPanel = null;
    // [Código para preservar o painel de nomes]
    
    messagesPanel.removeAll();
    messagesPanel.setLayout(new GridBagLayout());
    GridBagConstraints gbc = new GridBagConstraints();
    // [Configuração do layout]
    
    // Renderiza cada mensagem
    for (ChatMessage msg : chatMessages) {
        JPanel msgPanel = new JPanel(new FlowLayout(msg.isUser ? FlowLayout.RIGHT : FlowLayout.LEFT));
        msgPanel.setOpaque(false);
        String prefix = msg.isUser ? "Você: " : "";
        JTextArea msgArea = new JTextArea(prefix + msg.text);
        // [Configuração da aparência da mensagem]
        
        // Estiliza diferentemente mensagens do usuário e do bot
        msgArea.setBackground(msg.isUser ? new Color(220, 248, 198) : new Color(232, 232, 232));
        
        // [Adiciona a mensagem ao painel]
    }
    
    // [Configuração final do layout]
}
```

#### Indicador de Carregamento

O chat implementa um indicador de carregamento para mostrar quando o assistente está processando uma resposta:

```java
private void createLoadingIndicator() {
    loadingLabel = new JLabel("Assistente está digitando...");
    loadingLabel.setHorizontalAlignment(JLabel.CENTER);
    loadingLabel.setVisible(false);
    
    // Create timer for loading animation
    loadingTimer = new Timer(500, e -> {
        loadingDots = (loadingDots + 1) % 4;
        String dots = ".".repeat(loadingDots);
        loadingLabel.setText("Assistente está digitando" + dots);
    });
}

public void showLoading() {
    if (loadingLabel != null) {
        loadingLabel.setVisible(true);
        loadingTimer.start();
        messagesPanel.add(loadingLabel);
        messagesPanel.add(Box.createVerticalStrut(10));
        messagesPanel.revalidate();
        messagesPanel.repaint();
    }
}

public void hideLoading() {
    if (loadingLabel != null) {
        loadingTimer.stop();
        loadingLabel.setVisible(false);
        messagesPanel.remove(loadingLabel);
        messagesPanel.revalidate();
        messagesPanel.repaint();
    }
}
```

### Gerenciamento de Contexto

O chat permite adicionar conversas de WhatsApp como contexto para as perguntas, permitindo que o assistente responda com base nas informações contidas nessas conversas.

```java
public List<String> getContextChatNames() {
    return new ArrayList<>(chatNames);  // Return a copy to prevent external modification
}

public void addChatName(String name) {
    // Verifica se o chat já existe
    if (chatNames.contains(name)) {
        JOptionPane.showMessageDialog(this,
            "Este chat já foi adicionado ao contexto.",
            "Chat Duplicado",
            JOptionPane.WARNING_MESSAGE);
        return;
    }
    
    chatNames.add(name);
    chatColors.add(AVAILABLE_COLORS[chatNames.size() % AVAILABLE_COLORS.length]);
    updateChatNamesPanel();
}

public void removeChatName(String name) {
    int index = chatNames.indexOf(name);
    if (index != -1) {
        chatNames.remove(index);
        chatColors.remove(index);
        updateChatNamesPanel();
    }
}

public List<IItem> getContextChatItems() {
    return contextChatItems;
}

public void addContextChatItem(IItem item) {
    if (!this.contextChatItems.contains(item)) {
        this.contextChatItems.add(item);
    }
}
```

## Integração com API de IA

A comunicação com a API de IA é gerenciada pela classe `ResultTableListener`, que contém o método `sendToOpenAI` responsável por enviar as perguntas do usuário e o contexto relevante para a API.

### Método `sendToOpenAI`

```java
public static void sendToOpenAI(String chatContent, String userQuestion) {
    try {
        // Create HTTP Client
        HttpClient client = HttpClient.newBuilder().build();
        
        // Get the list of chats in context
        List<String> contextChatNames = App.get().getContextChatNames();
        List<IItem> contextChatItems = App.get().getContextChatItems();
        String contentToSend;
        
        // Determina qual conteúdo enviar com base no contexto
        if (contextChatNames.isEmpty()) {
            // Se não houver chats no contexto, envia resumos de todos os chats
            contentToSend = getAllChatSummaries();
        } else if (contextChatNames.size() == 1) {
            // Se houver apenas um chat no contexto, envia seu conteúdo completo
            IItem chat = contextChatItems.get(0);
            contentToSend = new String(chat.getBufferedInputStream().readAllBytes(), 
                java.nio.charset.StandardCharsets.UTF_8);
        } else {
            // Se houver múltiplos chats no contexto, envia seus resumos
            contentToSend = getContextChatSummaries(contextChatNames);
        }
        
        // Cria o corpo da requisição
        Map<String, Object> requestBody = new HashMap<>();
        requestBody.put("chat_content", contentToSend);
        requestBody.put("user_question", userQuestion);
        
        // Cria e envia a requisição HTTP
        HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create(API_URL))
            .header("Content-Type", "application/json")
            .POST(HttpRequest.BodyPublishers.ofString(objectMapper.writeValueAsString(requestBody)))
            .build();
        
        // Processa a resposta
        HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());
        
        // Extrai a resposta do assistente
        Map<String, Object> responseMap = objectMapper.readValue(response.body(), Map.class);
        String content = (String) responseMap.get("response");
        
        // Atualiza o chat com a resposta
        App.get().updateChatText(content);
        
    } catch (Exception e) {
        logger.error("Error sending request to API", e);
        App.get().updateChatText("Desculpe, ocorreu um erro ao processar sua solicitação.");
    }
}
```

### Obtenção de Resumos de Chat

Para otimizar o envio de informações para a API, o sistema utiliza resumos dos chats quando necessário:

#### `getAllChatSummaries()`

```java
private static String getAllChatSummaries() {
    StringBuilder summaries = new StringBuilder();
    try {
        // Busca todos os chats do WhatsApp
        IPEDSearcher searcher = new IPEDSearcher(App.get().appCase);
        searcher.setQuery("mediaType:whatsapp-chat");
        MultiSearchResult result = searcher.multiSearch();
        
        // Obtém os resumos de cada chat
        for (IItemId itemId : result.getIterator()) {
            IItem item = App.get().appCase.getItemByItemId(itemId);
            if (item != null) {
                String[] chunkSummaries = item.getMetadata().getValues(ExtraProperties.CHUNK_SUMMARY);
                if (chunkSummaries != null && chunkSummaries.length > 0) {
                    summaries.append("Chat: ").append(item.getName()).append("\n");
                    for (String summary : chunkSummaries) {
                        summaries.append(summary).append("\n");
                    }
                    summaries.append("\n");
                }
            }
        }
    } catch (Exception e) {
        logger.error("Error getting all chat summaries", e);
    }
    return summaries.toString();
}
```

#### `getContextChatSummaries(List<String> contextChatNames)`

```java
private static String getContextChatSummaries(List<String> contextChatNames) {
    StringBuilder summaries = new StringBuilder();
    try {
        // Obtém os itens de chat do contexto
        List<IItem> contextChatItems = App.get().getContextChatItems();
        
        // Processa cada item de chat
        for (IItem item : contextChatItems) {
            if (item != null) {
                // Tenta obter resumos de chunks dos metadados
                String[] chunkSummaries = item.getMetadata().getValues(ExtraProperties.CHUNK_SUMMARY);
                
                // Se não encontrar nos metadados, tenta atributos extras
                if (chunkSummaries == null || chunkSummaries.length == 0) {
                    Object extraAttr = item.getExtraAttributeMap().get(ExtraProperties.CHUNK_SUMMARY);
                    // [Código para extrair resumos de atributos extras]
                }
                
                // Adiciona os resumos ao conteúdo a ser enviado
                if (chunkSummaries != null && chunkSummaries.length > 0) {
                    summaries.append("\n=== Chat: ").append(item.getName()).append(" ===\n\n");
                    
                    for (String summary : chunkSummaries) {
                        if (summary != null && !summary.trim().isEmpty()) {
                            // Limpa e formata o resumo
                            String cleanSummary = summary.trim()
                                .replaceAll("\\s+", " ")  // Normaliza espaços em branco
                                .replaceAll("\\n+", "\n") // Normaliza quebras de linha
                                .trim();
                            
                            if (!cleanSummary.isEmpty()) {
                                summaries.append(cleanSummary).append("\n");
                            }
                        }
                    }
                }
            }
        }
        
        // Formata o resultado final
        String result = summaries.toString().trim();
        
        // Garante consistência nas quebras de linha
        result = result.replaceAll("\\r\\n", "\n")
                      .replaceAll("\\r", "\n")
                      .replaceAll("\\n\\s*\\n", "\n")
                      .trim();
                      
        return result;
        
    } catch (Exception e) {
        logger.error("Error getting context chat summaries", e);
        return "";
    }
}
```

## Fluxo de Funcionamento

1. **Inicialização**: O chat é inicializado com uma mensagem de boas-vindas do assistente.

2. **Interação do Usuário**: 
   - O usuário digita uma pergunta na área de entrada.
   - Ao pressionar Enter, a mensagem é adicionada ao chat e enviada para processamento.
   - Um indicador de carregamento é exibido enquanto a resposta é processada.

3. **Processamento do Contexto**:
   - Se não houver chats no contexto, são enviados resumos de todos os chats.
   - Se houver um único chat no contexto, seu conteúdo completo é enviado.
   - Se houver múltiplos chats no contexto, são enviados seus resumos.

4. **Comunicação com a API**:
   - A pergunta do usuário e o contexto são enviados para a API.
   - A API processa a pergunta e gera uma resposta.

5. **Exibição da Resposta**:
   - A resposta da API é adicionada ao chat.
   - O indicador de carregamento é ocultado.
   - A interface é atualizada para exibir a nova mensagem.

## Conclusão

O chat "Fala, Perito!" é uma ferramenta integrada ao IPED que utiliza modelos de linguagem para auxiliar os peritos na análise de evidências digitais. Ele permite que os usuários façam perguntas em linguagem natural e recebam respostas contextualizadas com base nas conversas de WhatsApp e outras evidências presentes no caso.

A implementação combina elementos de interface gráfica em Java Swing, processamento assíncrono de requisições HTTP e integração com APIs de IA para oferecer uma experiência de usuário fluida e respostas relevantes às consultas dos peritos.
