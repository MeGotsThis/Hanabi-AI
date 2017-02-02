# Multi Tag Bot v2.0

Derived from Full Tag Bot v1.5

Behavior Changes:
Likes to tags multiple cards such that:
- When given a color, it implies from newest 1, 2, 3, etc given there is no played cards of that color and no other values are marked in between
  - It will work around with known values
  - For example, if the hand from newest X1, X5, X2 and the X5 is known as a 5, the X color will likely be clued
- When given a value, it will wait for all played/clued values before that card and continues from there
  - If there are not enough colors to match, it will give that clue and assume the user will hold the card until marked or becomes the minimum playable value


## Scores

| Players   | Variant     | Avg. Score | Perfect Rate | Loss Rate | Avg. Non-Loss Score | Avg. Loss Score |
| --------- | ----------- | ---------- | ------------ | --------- | ------------------- | --------------- |
| 2 Players | No Variant  | 16.632     | 0.07%        | 7.53%     | 17.277              | 8.716           |
| 3 Players | No Variant  | 17.252     | 0.09%        | 1.51%     | 17.360              | 10.219          |
| 4 Players | No Variant  | 15.759     | 0%           | 0.54%     | 15.782              | 11.407          |
| 5 Players | No Variant  | 15.155     | 0%           | 0.15%     | 15.161              | 11.333          |

### 4 Players - No Variant

```
Bot: Multi-tag Bot v1.0
Variant: No Variant
Players: 4

Number of Games: 10000
Number of Best Score: 0
Number of Losses: 54
Average Score (all): 15.75860
Average Score (non-loss): 15.78222
Average Score (loss): 11.40741

Non-loss Score Distribution
Score 25: 0
Score 24: 21
Score 23: 105
Score 22: 284
Score 21: 527
Score 20: 676
Score 19: 788
Score 18: 1037
Score 17: 1067
Score 16: 1022
Score 15: 940
Score 14: 881
Score 13: 691
Score 12: 601
Score 11: 451
Score 10: 324
Score 9: 242
Score 8: 147
Score 7: 75
Score 6: 50
Score 5: 10
Score 4: 7
Score 3: 0
Score 2: 0
Score 1: 0
Score 0: 0

Loss Score Distribution
Score 0: 0
Score 1: 0
Score 2: 1
Score 3: 0
Score 4: 3
Score 5: 4
Score 6: 3
Score 7: 3
Score 8: 0
Score 9: 1
Score 10: 3
Score 11: 6
Score 12: 9
Score 13: 2
Score 14: 7
Score 15: 1
Score 16: 5
Score 17: 2
Score 18: 0
Score 19: 3
Score 20: 1
Score 21: 0
Score 22: 0
Score 23: 0
Score 24: 0
Score 25: 0
```

### 5 Players - No Variant

```
Number of Games: 10000
Number of Best Score: 0
Number of Losses: 15
Average Score (all): 15.15480
Average Score (non-loss): 15.16054
Average Score (loss): 11.33333

Non-loss Score Distribution
Score 25: 0
Score 24: 1
Score 23: 21
Score 22: 99
Score 21: 325
Score 20: 593
Score 19: 763
Score 18: 955
Score 17: 1032
Score 16: 1067
Score 15: 1053
Score 14: 968
Score 13: 919
Score 12: 678
Score 11: 493
Score 10: 391
Score 9: 248
Score 8: 186
Score 7: 106
Score 6: 56
Score 5: 22
Score 4: 7
Score 3: 2
Score 2: 0
Score 1: 0
Score 0: 0

Loss Score Distribution
Score 0: 0
Score 1: 0
Score 2: 0
Score 3: 0
Score 4: 1
Score 5: 0
Score 6: 0
Score 7: 0
Score 8: 2
Score 9: 3
Score 10: 0
Score 11: 2
Score 12: 3
Score 13: 0
Score 14: 0
Score 15: 1
Score 16: 1
Score 17: 2
Score 18: 0
Score 19: 0
Score 20: 0
Score 21: 0
Score 22: 0
Score 23: 0
Score 24: 0
Score 25: 0
```

### 3 Players - No Variant

```
Bot: Multi-tag Bot v1.0
Variant: No Variant
Players: 3

Number of Games: 10000
Number of Best Score: 9
Number of Losses: 151
Average Score (all): 17.25210
Average Score (non-loss): 17.35994
Average Score (loss): 10.21854

Non-loss Score Distribution
Score 25: 9
Score 24: 67
Score 23: 276
Score 22: 557
Score 21: 803
Score 20: 1081
Score 19: 1133
Score 18: 1233
Score 17: 1097
Score 16: 941
Score 15: 796
Score 14: 559
Score 13: 450
Score 12: 332
Score 11: 202
Score 10: 134
Score 9: 87
Score 8: 59
Score 7: 21
Score 6: 10
Score 5: 2
Score 4: 0
Score 3: 0
Score 2: 0
Score 1: 0
Score 0: 0

Loss Score Distribution
Score 0: 0
Score 1: 0
Score 2: 3
Score 3: 5
Score 4: 9
Score 5: 14
Score 6: 17
Score 7: 8
Score 8: 3
Score 9: 13
Score 10: 8
Score 11: 12
Score 12: 3
Score 13: 10
Score 14: 7
Score 15: 11
Score 16: 10
Score 17: 11
Score 18: 5
Score 19: 1
Score 20: 1
Score 21: 0
Score 22: 0
Score 23: 0
Score 24: 0
Score 25: 0
```

### 2 Players - No Variant

```
Bot: Multi-tag Bot v1.0
Variant: No Variant
Players: 2

Number of Games: 10000
Number of Best Score: 7
Number of Losses: 753
Average Score (all): 16.63240
Average Score (non-loss): 17.27706
Average Score (loss): 8.71580

Non-loss Score Distribution
Score 25: 7
Score 24: 42
Score 23: 167
Score 22: 403
Score 21: 698
Score 20: 994
Score 19: 1123
Score 18: 1194
Score 17: 1136
Score 16: 997
Score 15: 832
Score 14: 582
Score 13: 417
Score 12: 297
Score 11: 172
Score 10: 107
Score 9: 48
Score 8: 21
Score 7: 6
Score 6: 3
Score 5: 1
Score 4: 0
Score 3: 0
Score 2: 0
Score 1: 0
Score 0: 0

Loss Score Distribution
Score 0: 0
Score 1: 1
Score 2: 30
Score 3: 44
Score 4: 70
Score 5: 80
Score 6: 71
Score 7: 58
Score 8: 56
Score 9: 45
Score 10: 49
Score 11: 41
Score 12: 35
Score 13: 32
Score 14: 40
Score 15: 36
Score 16: 16
Score 17: 27
Score 18: 10
Score 19: 9
Score 20: 1
Score 21: 2
Score 22: 0
Score 23: 0
Score 24: 0
Score 25: 0
```
