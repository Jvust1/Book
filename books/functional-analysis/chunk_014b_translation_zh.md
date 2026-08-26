# chunk_014b 中文学习层（PDF 271-280 / 纸质 252-261）

> 本文件是学习层，不替代原书。定理编号、公式编号、页码与结构锚点均以原 PDF 为证据层。

# Chapter 6 An Introduction to Brownian Motion

## §4 Some further properties of Brownian motion / Brownian motion 的进一步性质

### Theorem 4.2：Hölder 正则性与路径粗糙性

上一批已给出 part (a)：几乎处处 Brownian 路径在任意有限时间区间上，对每个 `a<1/2` 都满足局部 `a`-Hölder 控制。

PDF 271 给出 part (b)：若 `a>1/2`，则对几乎每条路径 p，且对每个固定 `t≥0`，

`limsup_{h→0} |p(t+h)-p(t)| / h^a = ∞`。

证明先利用 Theorem 3.1 构造 Brownian motion 时已经得到的紧集 `K(T)` 完成 part (a)。对 part (b)，选整数 k 使 `dk(a-1/2)>1`，再把存在某个时刻 `t_0` 的小增量条件离散化为式 (11)。独立增量与 Brownian scaling 把相应概率压到 Gaussian 小球概率；所得上界随 n→∞ 趋于 0，于是排除任何 `a>1/2` 的局部 Hölder 控制。

这说明 Brownian 路径的自然临界正则性指数是 `1/2`：小于 `1/2` 的 Hölder 控制几乎处处成立，而大于 `1/2` 的控制几乎处处彻底失败。

教材随后把这种 nowhere-smooth 行为与前几卷中的 lacunary Fourier series、von Koch fractal、Baire category generic continuous functions 联系起来。

### 随机游走路径对固定连续路径的有限维逼近

固定路径 `q∈P`、时间点 `t_1,...,t_n` 与 `ε>0`，令 `O_ε` 表示在这些时间坐标上与 q 相差小于 ε 的开集合。由 `μ_N⇒W` 与边界为 Wiener-null 的事实，式 (12) 给出对应随机游走路径束的概率收敛到 `W(O_ε)`。

# §5 Stopping times and the strong Markov property / 停止时刻与强 Markov 性质

本节目标是把 Brownian motion 与 Dirichlet problem 联系起来。给定有界开集 `R⊂R^d` 与边界连续函数 f，希望寻找在 R 内 harmonic、在闭包连续且边界值为 f 的函数 u。

从 `x∈R` 出发的 Brownian motion 写作 `B_t^x=x+B_t`。令 `τ_x` 为它第一次离开 R 的时刻；退出点 `B^x_{τ_x}` 在 `∂R` 上诱导概率测度

`μ^x(E)=P(B^x_{τ_x}∈E)`，

即 harmonic measure。教材指出，在适当的区域条件下，Dirichlet 解由

`u(x)=∫_{∂R} f(y)dμ^x(y)`

给出。

PDF 273 的 Figure 1 直观展示了一条从 x 出发、在 `τ(ω)` 时刻穿出 R 的路径。该图已单独保存为 `figures/fig_ch6_01_exit_path_at_tau.png`。

## §5.1 Stopping times and the Blumenthal zero-one law

### 离散 stopping time

若 `{s_n}` 是相对于递增 σ-代数 `{A_n}` 的 martingale，整数值函数 τ 若满足 `{τ=n}∈A_n`（等价地 `{τ≤n}∈A_n`），则称 τ 为 stopping time。

若 `τ≤N`，式 (13) 给出

`∫ s_τ dm = ∫ s_N dm`。

证明把 `{τ=n}` 分块，再利用 martingale 条件在每块上把 `s_n` 的积分换成 `s_N`。

### Brownian motion 的连续时间 martingale 结构

令 `A_t` 由 `B_s,0≤s≤t` 生成（并补上零测集的子集）。任取递增时间序列，`B_{t_n}` 构成 martingale；同时路径几乎处处连续。

由上一章的 martingale maximal inequality 可直接得到式 (14)：

`P(sup_{0≤t≤T}|B_t|>α) ≤ α^{-1}||B_T||_{L^1}`。

连续时间 stopping time 的定义是：非负 τ 对每个 t 都满足 `{τ≤t}∈A_t`。

### exit time 与 Proposition 5.1

定义

`τ_x=inf{t≥0:B_t^x∉R}`，

`τ_x*=inf{t>0:B_t^x∉R}`。

**Proposition 5.1**：两者都是 stopping times。

证明先用有理时间刻画连续路径进入开集 O 的事件；再取 `O_n={x:d(x,R^c)<1/n}`，得到式 (15) `{τ≤t}=∩_n{τ_{O_n}<t}`。对严格退出时间在 t=0 的细节，需要研究

`A_{0+}=∩_{t>0}A_t`。

### Lemma 5.2 / Blumenthal zero-one law

**Lemma 5.2** 断言 `A_{0+}=A_0`。因此任意在任意小正时间都已可测的事件必为平凡事件（概率 0 或 1），这就是 Blumenthal zero-one law。

证明用 Brownian 独立增量：对 `A∈A_{0+}` 和有限组时间点，先把所有增量平移 δ，再让 `δ→0`；得到 A 与所有 cylindrical events 独立。再扩张到全部 Borel 事件，最终 `P(A)=P(A)^2`。

由此，对边界点 x，事件 `{τ_x*=0}` 的概率只能是 0 或 1。若为 1，称 x 为 **regular boundary point**：几乎所有从 x 出发的 Brownian 路径在任意小正时间内都会到 R 外。

教材还指出 `τ_x(ω)` 对 `(x,ω)` 联合可测。

## §5.2 The strong Markov property / 强 Markov 性质

对 stopping time σ，定义 `A_σ`：集合 A 属于 `A_σ` 当且仅当对每个 t，`A∩{σ≤t}∈A_t`。

### Theorem 5.3

定义重新启动后的过程

`B_t*=B_{t+σ}-B_σ`。

**Theorem 5.3**：`B_t*` 仍是 Brownian motion，并且与过去信息 `A_σ` 独立。

证明先处理 σ 为常数，再处理取可数值的离散 σ。对 Borel 集 E 与 `A∈A_σ`，得到式 (16)：

`P({B*∈E}∩A)=P(B∈E)P(A)`。

一般 stopping time 用向上取整到 dyadic 网格的 `σ^(n)` 逼近，满足 `σ^(n)↓σ` 且 `A_σ⊂A_{σ^(n)}`。由路径连续性与上一章关于开集/Borel 集的极限工具，将离散情形的独立性传到一般 σ。相同逼近也说明 `B_σ` 对 `A_σ` 可测。

## §5.3 Other forms of the strong Markov Property

令 `P~` 为所有 `[0,∞)→R^d` 连续路径，不要求从 0 出发。每条路径可唯一写成 `(p,x)∈P×R^d`，所以 `P~=P×R^d`。

### Theorem 5.4

对 `P~` 上任意 bounded Borel function f，式 (17) 表达：在 stopping time σ 之后看到的整条未来路径，其分布等于“一条独立的新 Brownian 路径 + 随机起点 `B_σ`”。

证明先对乘积函数 `f_1(p,x)=f_2(p)f_3(x)` 利用 Theorem 5.3 的同分布与独立性，再通过矩形 Borel 集生成的 σ-代数与简单函数逼近推广到任意 bounded Borel f。

PDF 280 最后开始准备与 Dirichlet problem 最直接相关的版本。对区域 R 的退出时刻 `τ_y`，定义 stopped process

`B̂_t^y = y + B_{t∧τ_y}`。

其后续性质与两个 stopping times `σ≤τ` 的版本在 PDF 281 继续，本批不提前补写。
