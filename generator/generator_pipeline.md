flowchart TD
    A[Start] --> B{Topic Input Mode}
    
    B -->|Random Mode| C[Select from Curated<br/>Topic Database<br/>~100 topics in XML]
    B -->|User Input Mode| D[Process User Input<br/>Extract Core Subject]
    
    C --> E[Topic Selected]
    D --> E
    
    E --> F[Stage 1: Category Selection<br/>LLM analyzes topic and selects<br/>3-5 humor categories from<br/>50-70 categories in XML]
    
    F --> G[Stage 2: Factor Selection<br/>For each category, LLM selects<br/>3-5 specific factors/styles<br/>from separate XML structure]
    
    G --> H[Create Category-Factor Pairs<br/>~10 individual pairs generated]
    
    H -->     I[Stage 3: Hook Point Generation<br/>For each C-F pair:<br/>Generate 1-10 hook points<br/>• Semantically related<br/>• Phonetically compatible<br/>• Culturally relevant<br/>• Conceptually surprising]
    
    I --> J[Stage 4: Cross-Category Analysis<br/>Analyze all hook points across<br/>different C-F pairs for:<br/>• Identical words<br/>• Semantic similarities<br/>• Phonetic similarities]
    
    J --> K{Similarities Found?}
    
    K -->|Yes| L[Stage 5: Composite Groups Generation<br/>Combine C-F pairs with<br/>shared/similar hook points<br/>~10 synthesized groups]
    K -->|No| M[Keep Individual C-F Pairs]
    
    L --> N[Final Generation Set<br/>~60 unique contexts:<br/>• Individual C-F pairs<br/>• Grouped C-F pairs]
    M --> N
    
    N --> O[Stage 6: Joke Generation Engine<br/>Each context generates 3-5 jokes<br/>using enriched prompts with:<br/>• Original topic<br/>• C-F pairs<br/>• Hook points<br/>• Humor guidelines]
    
    O --> P[Joke Portfolio<br/>~240 total jokes generated<br/>across all contexts]
    
    P --> Q[Stage 7: Rating Judge<br/>Evaluate and score<br/>all generated jokes]
    
    Q --> R[Select Top 20<br/>Highest rated jokes]
    
    R --> S[Stage 8: Duel Judge<br/>Pairwise comparison<br/>to determine final winner]
    
    S --> T[Final Winner<br/>Best joke selected]
    
    %% Future Integration - Evolutionary Algorithm (RED Pipeline)
    R -.->|Future Integration| U[Evolutionary Algorithm<br/>Learns from top-rated jokes<br/>to optimize selection parameters]
    
    U -.->|Surviving Categories| F
    U -.->|Surviving Factors| G  
    U -.->|Surviving Hooks| I
    U -.->|Surviving Cross-Categories| J
    
    style A fill:#e1f5fe,color:#000000
    style T fill:#c8e6c9,color:#000000
    style F fill:#fff3e0,color:#000000
    style G fill:#fff3e0,color:#000000
    style I fill:#f3e5f5,color:#000000
    style J fill:#f3e5f5,color:#000000
    style L fill:#e8f5e8,color:#000000
    style O fill:#fce4ec,color:#000000
    style Q fill:#fff9c4,color:#000000
    style S fill:#ffecb3,color:#000000
    style U fill:#ffcdd2,stroke:#d32f2f,stroke-width:2px,color:#000000
    
    %% RED dotted lines for future integration
    linkStyle 25 stroke:#d32f2f,stroke-width:2px,stroke-dasharray: 5 5
    linkStyle 21 stroke:#d32f2f,stroke-width:2px,stroke-dasharray: 5 5
    linkStyle 22 stroke:#d32f2f,stroke-width:2px,stroke-dasharray: 5 5
    linkStyle 23 stroke:#d32f2f,stroke-width:2px,stroke-dasharray: 5 5
    linkStyle 24 stroke:#d32f2f,stroke-width:2px,stroke-dasharray: 5 5