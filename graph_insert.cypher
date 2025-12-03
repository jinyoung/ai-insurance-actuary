// --- Chunk 1 (Page 1) ---

Here are the Cypher MERGE statements to construct the graph based on the provided text:

```
MERGE (c1:Concept {name: "실손건강보험"})
MERGE (c2:Concept {name: "손해보험"})
MERGE (c3:Concept {name: "대수의 법칙"})
MERGE (c4:Concept {name: "영업보험료"})
MERGE (c5:Concept {name: "순보험료"})
MERGE (c6:Concept {name: "부가보험료"})
MERGE (c7:Concept {name: "장기계약생명보험"})
MERGE (c8:Concept {name: "장기손해보험"})
MERGE (c9:Concept {name: "일반손해보험"})
MERGE (c10:Concept {name: "보험수리적 접근"})
MERGE (c11:Concept {name: "보험경계학적 접근"})
MERGE (c12:Concept {name: "최적판매가격"})
MERGE (c13:Concept {name: "예정이윤"})
MERGE (c14:Concept {name: "생명보험"})
MERGE (c15:Concept {name: "실손형 건강보험"})

MERGE (d1:Definition {text: "실손건강보험의 원리는 손해보험의 그것과 유사하다. 동일위험을 안고 있는 다수의 경제단위가 하나의 위험집단을 구성해서 각자가 납출한 보험료에 의해 구성원 일부가 입는 의료비 손해를 보상함으로써 의료비에 의한 경제적 충격을 최소화하는 위험의 분담이 그 운영원리이다."})
MERGE (d2:Definition {text: "대수의 법칙은 동일위험에 당면하고 있는 사람이 장래에 사고 발생의 경향을 예측할 수 있을 정도로 다수가 있어야 한다는 원칙이다."})
MERGE (d3:Definition {text: "영업보험료는 보험가입자가 보험자에게 위험보장의 대가로서 지불하는 금액을 의미하며, 이는 보험금 지급에 충당되는 부분인 순보험료와 사업비 지급에 충당되는 부분인 부가보험료로 구성된다."})
MERGE (d4:Definition {text: "부가보험료는 장기계약생명보험과 장기손해보험에서 예정사업비(유지비, 수금비)를 의미하며, 일반(단기)손해보험에서는 예정이윤을 포함한다."})
MERGE (d5:Definition {text: "보험경계학적(재무적) 가격산정방법은 보험사의 예정이윤에 관한 기본적인 정보를 제공하며, 최적가격에 대한 정보를 획득할 수 있게 하는 방법이다."})

MERGE (c1)-[:DEFINES]->(d1)
MERGE (c3)-[:DEFINES]->(d2)
MERGE (c4)-[:DEFINES]->(d3)
MERGE (c6)-[:DEFINES]->(d4)
MERGE (c11)-[:DEFINES]->(d5)

MERGE (c1)-[:RELATED_TO]->(c2)
MERGE (c4)-[:COMPOSED_OF]->(c5)
MERGE (c4)-[:COMPOSED_OF]->(c6)
MERGE (c6)-[:RELATED_TO]->(c7)
MERGE (c6)-[:RELATED_TO]->(c8)
MERGE (c6)-[:RELATED_TO]->(c9)
MERGE (c11)-[:RELATED_TO]->(c13)
MERGE (c11)-[:RELATED_TO]->(c12)
MERGE (c14)-[:RELATED_TO]->(c15)
```

// --- Chunk 2 (Page 2) ---

```
MERGE (c1:Concept {name: "영업보험료"})
MERGE (d1:Definition {text: "적정해야 하고, 과도해서도 안되며, 공정하게 산출되어야 한다. 보험자는 보험자의 지급능능 상태가 발생하지 않는 수준이어야 한다(순보험료의 적정성 확보). 그러나 일반적으로 적정한 보험료란 투자손익을 감안하여 보험금과 사업비를 적절히 지급할 수 있도록 하는 상태의 요율(영업보험료의 적정성)을 말한다."})
MERGE (c1)-[:DEFINES]->(d1)

MERGE (c2:Concept {name: "순보험료"})
MERGE (d2:Definition {text: "보험자의 지급능능 상태가 발생하지 않는 수준이어야 한다(순보험료의 적정성 확보)."})
MERGE (c2)-[:DEFINES]->(d2)

MERGE (c3:Concept {name: "적정성"})
MERGE (d3:Definition {text: "보험자의 지급능능에 대비한 요율의 수준을 강조한 것이기 때문에, 상한선이 없이 보험가입자에게 과도하거나 불공정한 가격을. 보험자가 결정할 가능성이 있다."})
MERGE (c3)-[:DEFINES]->(d3)

MERGE (c4:Concept {name: "비과도성"})
MERGE (d4:Definition {text: "보험료가 과도하지 않도록 해야 한다."})
MERGE (c4)-[:DEFINES]->(d4)

MERGE (c5:Concept {name: "공정성"})
MERGE (d5:Definition {text: "보험가입자의 개별위험에 대하여 공정하게 요율을 결정해야 한다."})
MERGE (c5)-[:DEFINES]->(d5)

MERGE (c6:Concept {name: "전통적 순보험료법"})
MERGE (d6:Definition {text: "사고발생률(빈도)와 사고건당 본인부담금(심도)을 토대로 동일위험집단에 대한 위험도를 수리적 또는 통계적 분석방법으로 예측하여 보험료를 산정하는 방법이다."})
MERGE (c6)-[:DEFINES]->(d6)

MERGE (c7:Concept {name: "실손형 건강보험"})
MERGE (d7:Definition {text: "순보험료(P)는 1인당 평균본인부담의료비이다."})
MERGE (c7)-[:DEFINES]->(d7)

MERGE (v1:Variable {name: "P"})
MERGE (v2:Variable {name: "I"})
MERGE (v3:Variable {name: "N"})
MERGE (v4:Variable {name: "L"})
MERGE (v5:Variable {name: "B"})

MERGE (f1:Formula {expression: "P = I * L"})
MERGE (v1)-[:USED_IN]->(f1)
MERGE (v2)-[:USED_IN]->(f1)
MERGE (v4)-[:USED_IN]->(f1)

MERGE (f2:Formula {expression: "I = N"})
MERGE (v2)-[:USED_IN]->(f2)
MERGE (v3)-[:USED_IN]->(f2)

MERGE (c1)-[:RELATED_TO]->(c2)
MERGE (c1)-[:RELATED_TO]->(c3)
MERGE (c1)-[:RELATED_TO]->(c4)
MERGE (c1)-[:RELATED_TO]->(c5)
MERGE (c2)-[:RELATED_TO]->(c6)
MERGE (c7)-[:RELATED_TO]->(c2)
```
