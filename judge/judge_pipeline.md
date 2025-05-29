flowchart TD
    %% Rating Judge Pipeline
    subgraph RJ ["Rating Judge Pipeline"]
        Start([Input Joke]) --> Stage1{Stage 1: Admissibility Assessment<br/>Liberal Evaluation:<br/>Intent ✓ Complete ✓<br/>Appropriate ✓ Coherent ✓<br/>Accessible ✓}
        
        Stage1 -->|Accept| Stage2[Stage 2: Category Classification]
        Stage1 -->|Reject| Reject1[❌ Rejected]
        
        XMLCat[(criteria_categories_jokes.xml)]
        XMLFact[(factors_to_judge_jokes.xml)]
        
        XMLCat --> Branch1
        XMLFact --> Branch2
        
        Stage2 --> Branch1{Categories Found?}
        Branch1 -->|Yes| StdCat[Standard Categories<br/>Multi-assignment allowed]
        Branch1 -->|No| DynFact[Generate Dynamic Factors<br/>+ Examples]
        
        StdCat --> Stage3[Stage 3: Factor Identification]
        
        Stage3 --> Branch2{Relevant Factors?}
        Branch2 -->|Yes| ExistFact[Use Existing Factors<br/>from XML]
        Branch2 -->|No| DynFact
        
        ExistFact --> Stage4[Stage 4: Factor Scoring<br/>Convergence Point]
        DynFact --> Stage4
        DynFact --> Stage4
        
        Stage4 --> Final1[Final Rating<br/>Max Score, Mean Score<br/>Individual Factor Scores]
    end
    
    %% Duel Judge Pipeline
    subgraph DJ ["Duel Judge Pipeline"]
        StartDuel([Input: Joke A + Joke B]) --> Parallel1{Parallel Comparison}
        
        Parallel1 --> CompAB[Compare A vs B<br/>Position 1]
        Parallel1 --> CompBA[Compare B vs A<br/>Position 2]
        
        CompAB --> Combine[Stage 2: Result Combination]
        CompBA --> Combine
        
        Combine --> Consistency{Consistency Check}
        Consistency -->|Consistent| FinalDuel[Final Decision<br/>+ Confidence Factor<br/>1.0-10.0+ scale]
        Consistency -->|Inconsistent| Resolve[Conflict Resolution<br/>Lower Confidence]
        Resolve --> FinalDuel
    end
    
    %% Styling
    classDef stage fill:#e1f5fe,stroke:#01579b,stroke-width:2px,color:#000000
    classDef decision fill:#fff3e0,stroke:#e65100,stroke-width:2px,color:#000000
    classDef branch fill:#f3e5f5,stroke:#4a148c,stroke-width:2px,color:#000000
    classDef final fill:#e8f5e8,stroke:#1b5e20,stroke-width:2px,color:#000000
    classDef xml fill:#fff9c4,stroke:#f57f17,stroke-width:2px,color:#000000
    classDef reject fill:#ffebee,stroke:#c62828,stroke-width:2px,color:#000000
    
    class Stage1,Stage2,Stage3,Stage4,CompAB,CompBA,Combine stage
    class Branch1,Branch2,Parallel1,Consistency decision
    class StdCat,ExistFact,DynFact,Resolve branch
    class Final1,FinalDuel final
    class XMLCat,XMLFact xml
    class Reject1 reject