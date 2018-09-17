```c
            pcFSPassD->pcAlcD = pcFSPassD->pcVecAlcD[ iter ];
            pcFSPassD->pcPEnvD = pcFSPassD->pcVecPEnvD[ iter ];
            pcFSPassD->pcLPceD = pcFSPassD->pcAlcLPceD[ iter ];
```



```c
        pcStdD    = pcFSPassD->pcFSStdD[ iter ];
        pcCRLCD   = pcStdD->pcCRLCD;
        pcAlcD    = pcFSPassD->pcAlcD;
        pcUFDD    = pcStdD->pcUFDD;
        pcLRGD    = pcStdD->pcLRGD;
        pcLPceD   = pcFSPassD->pcLPceD;
        pcPEnvD   = pcFSPassD->pcPEnvD;
        pcEnPceD  = pcStdD->pcEnPceD;
        pcExPceD  = pcStdD->pcExPceD;
        pcPrvAct = pcFSPassD->pcPrvAct; // create a pointer to the previous active 
```

# 板形分配计算

板形的分配计算要分成几个大块：窜辊位置和弯辊力的确定、前后机架单位凸度的分配等。

## 分配中窜弯辊的确定

在进入板形分配模块的大门后，第一个面对的问题是从F7（往前）开始的窜辊位置和弯辊力大小确定。

因为F7出口的目标凸度和目标厚度是确定的，所以F7的出口目标凸度是确定的，迎面而来的是F7的窜辊位置计算。

模型采用辊系凸度的概念。各个辊系分量的代数和。

这里有三个不同的辊系凸度需要做一下辨别。第一个是前一卷带钢的辊系凸度，第二个是由目标单位凸度确定的辊系凸度，这个辊系凸度是我们所需的凸度，是我们当前机架进行板形分配计算的目标，还有一个凸度是窜辊位置确定后的辊形凸度，这是我们当前机架进行板形分配计算的结果。

所谓窜辊位置的确定，就是从前一卷带钢的辊系凸度出发，向着所需的辊系凸度进发，分配计算寻找合适的辊系凸度。这个合适的辊系凸度中的grn等效凸度对应的窜辊，就是板形分配的窜辊位置。

怎么寻找？模型中很直接，假设第二个辊系凸度和原始的辊系凸度之间的差值，全部由窜辊的变化来承担，用变化后的轧辊窜辊的等效凸度迭代计算出窜辊位置。迭代计算出的窜辊位置对应当前比例凸度分配状态下的辊系凸度，这时的辊系凸度即为分配的辊系凸度，这个辊系凸度一般和目标辊系凸度相同，如果不相同，说明窜辊位置被软极限限幅，所需的窜辊位置已经超出了窜辊软极限的范围。如果窜弯辊确定后的实际分配的辊系凸度无法达到目标辊系凸度的要求，那么当前辊系凸度对应的均载辊缝凸度一定达不到目标均载辊缝凸度的要求，因此需要重新对出入口目标单位凸度进行分配。





每个大循环中，首先crlc。Crns计算的是一个初始的辊系凸度。基本上为之前一块带钢的辊系凸度，之后分配时会发生变化。

