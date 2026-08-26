# chunk_014a 中文学习层（PDF 261-270 / 纸质 242-251）

> 本文件是学习层，不替代原书。公式、定理编号、页码与结构锚点均以原 PDF 为证据层。

# Chapter 6 An Introduction to Brownian Motion

## §2 Technical Preliminaries / 技术预备

### 路径空间度量的三个基本事实

上一批定义了

`d_n(p,p') = sup_{0≤t≤n}|p(t)-p'(t)|`

以及

`d(p,p') = Σ_{n≥1}2^{-n} d_n(p,p')/(1+d_n(p,p'))`。

PDF 261 补完三个基本结论：

1. `d(p_k,p)→0` 当且仅当 `p_k→p` 在 `[0,∞)` 的每个紧子区间上一致收敛；
2. `P` 在度量 `d` 下是完备空间；
3. `P` 是可分空间。

这三点使路径空间成为后续概率测度弱收敛分析的合适底层空间。

### Borel sets 与 cylindrical sets

令 `B` 为路径空间 `P` 的 Borel σ-代数，即由开集生成。因为 `P` 可分，`B` 也由开球生成。

固定 `0≤t_1≤...≤t_k`，并令 `A⊂R^{dk}` 为 Borel 集，则

`{p∈P : (p(t_1),...,p(t_k))∈A}`

称为 cylindrical set。由所有这类集合生成的 σ-代数记作 `C`。

**Lemma 2.1** 说明 `C=B`。一个方向很直接：若 `O⊂R^{dk}` 开，则对应的 cylindrical preimage 在 `P` 中开，因此 `C⊂B`。反方向利用连续路径的性质：在固定 `[0,n]` 上的 sup 条件可只在有理时间点检查，因此相应闭球式约束属于 `C`；进一步得到 `d`-开球属于 `C`，于是 `B⊂C`。

### finite-dimensional sections

对路径空间上的概率测度 `μ`，定义式 (4)：

`μ^(t_1,...,t_k)(A)=μ({p∈P:(p(t_1),...,p(t_k))∈A})`。

这是 `μ` 在时刻 `t_1,...,t_k` 的有限维 section（也就是对应坐标向量的分布）。由 Lemma 2.1 可知：若两个路径测度所有有限维 sections 都相同，则两个测度相同。

### 路径测度的弱收敛与 tightness

教材用式 (5) 定义 `μ_N⇒μ`：

`∫_P f dμ_N → ∫_P f dμ`，对每个 `f∈C_b(P)`。

路径空间 `P` 不是 σ-compact，因此不能直接套用一些简单紧性论证。这里引入 tightness：对每个 `ε>0`，存在紧集 `K_ε⊂X`，使

`μ_N(K_ε^c)≤ε` 对所有 N 成立。  (6)

**Lemma 2.2（Prokhorov）**：若 `{μ_N}` tight，则存在弱收敛子列。

书中的证明先在每个 `K_{1/m}` 上选取 `C(K_{1/m})` 的可数稠密函数族，再用 Tietze extension 扩张到整个 `X`；对可数函数族做对角化，得到使积分都收敛的子列。随后用 tightness 控制紧集外误差，把极限扩张到所有 `C_b(X)`，最后调用 Chapter 1 的测度表示定理得到极限概率测度。

**Corollary 2.3**：若 `{μ_N}` tight，并且对每组时间 `t_1,...,t_k`，有限维 sections `μ_N^(t_1,...,t_k)` 都弱收敛到给定的 `μ_{t_1,...,t_k}`，则整个序列 `μ_N` 弱收敛到某个路径测度 `μ`，且它的有限维 sections 正好等于这些极限。

证明要点是：任何由 tightness 抽出的弱收敛子列，其有限维 section 都必须等于同一给定极限；而有限维 sections 又唯一决定路径测度，因此所有可能子列极限相同，迫使整个序列收敛。

### Lemma 2.4：路径集的紧性判据

设闭集 `K⊂P`。若对每个 `T>0`，存在有界正函数 `w_T(h)`，满足 `w_T(h)→0`（`h→0`），并且

`sup_{p∈K} sup_{0≤t≤T}|p(t+h)-p(t)| ≤ w_T(h)`，  (7)

则 `K` 紧。条件 (7) 给出了每个有限区间上的统一等度连续性，本质上是 Arzelà-Ascoli 判据在路径空间中的应用。

# §3 Construction of Brownian motion / Brownian motion 的构造

目标是在 `(P,W)` 上构造 Wiener measure，使坐标过程 `B_t(p)=p(t)` 满足 Brownian motion 的 B-1/B-2/B-3。

对上一章的简单随机游走，缩放并线性插值得到路径 `S_t^(N)`。映射 `i_N:Z_{2d}^∞→P` 把每个样本送到相应路径，原产品测度 `m` 因而在 `P` 上诱导概率测度 `μ_N`。

## Theorem 3.1

`μ_N` 在 `P` 上弱收敛；极限就是 Wiener measure `W`。

证明分两步：

1. 证明 `{μ_N}` tight；
2. 用中心极限定理证明所有有限维 sections 收敛到 Brownian motion 的 Gaussian sections，再由 Corollary 2.3 得到路径测度弱收敛。

### Lemma 3.2：随机游走最大偏差尾界

对未缩放随机游走 `s_n=Σ_{k≤n}r_k`，任意 `p≥2` 有

`sup_{n≥1} m({sup_{k≤n}|s_k|>λ n^{1/2}})=O(λ^{-p})`，`λ→∞`。  (8)

证明把 `s_k` 在时刻 n 后停止，应用上一章的 martingale maximal theorem，得到式 (9)：

`m({s_n^*>α}) ≤ α^{-1}∫_{|s_n|>α}|s_n|dm`。

再积分得到 `||s_n^*||_p^p` 受 `||s_n||_p^p` 控制；最后用 Khinchin inequality 把 `L^p` 范数降到 `L^2`，而 `||s_n||_2=n^{1/2}`，于是取得所需尾界。

### tightness 的核心模连续性估计

固定 `0<a<1/2`。对给定 `ε`，选择足够大的 `c_1`，使式 (10) 成立：

`m({sup_{0≤t≤1,0≤h≤δ}|S_{t+h}^{(N)}-S_t^{(N)}|>c_1δ^a for some δ≤1})≤ε`。

证明先只看 dyadic `δ=2^{-k}`，把 `[0,1]` 分成长度 δ 的子区间；利用随机游走的 stationarity，把任意分块上的增量概率归约到从 0 开始的增量，再调用 Lemma 3.2。取 `σ=c_1δ^a` 后得到 `O(c_1^{-p}2^{-kb})`，其中 `b=-1+(1/2-a)p`。因为 `a<1/2`，可选足够大的 p 使 `b>0`，再对 k 求和。

同理可对任意有限 `T` 得到集合 `K(T)`。令 `ε_n=ε/2^n` 并取 `K=∩_n K(n)`，则 `μ_N(K^c)≤ε`；Lemma 2.4 保证 K 紧，因此 `{μ_N}` tight。

### finite-dimensional convergence

对固定 `0≤t_1≤...≤t_k`，多维中心极限定理给出增量

`S_{t_j}^{(N)}-S_{t_{j-1}}^{(N)}`

弱收敛到协方差为 `(t_j-t_{j-1})I` 的 Gaussian。由于增量独立，整个向量

`(S_{t_1}^{(N)},...,S_{t_k}^{(N)})`

的分布弱收敛到 Brownian motion 所要求的有限维 section。结合 tightness 与 Corollary 2.3，得到 `μ_N⇒W`。

### Donsker invariance principle

教材随后指出：简单随机游走不是必要的。若 `f_n` 是 iid、`R^d` 值、平方可积、均值 0、协方差矩阵为 I 的随机变量，按同样的 `1/√N` 空间缩放、`1/N` 时间缩放与线性插值构造路径，则诱导路径测度仍弱收敛到 Wiener measure。这就是 **Donsker invariance principle**。上一章 random flight 是一个具体例子。

# §4 Some further properties of Brownian motion / Brownian motion 的进一步性质

## Theorem 4.1：三个不变性

以下过程仍是 Brownian motion：

1. **缩放不变性**：对固定 `δ>0`，`δ^{-1/2}B_{tδ}`；
2. **正交变换不变性**：若 `o` 是 `R^d` 上正交线性变换，则 `o(B_t)`；
3. **固定时刻后的平移增量**：对固定 `σ_0≥0`，`B_{t+σ_0}-B_{σ_0}`。

验证只需逐项检查 B-1/B-2/B-3；关键是 covariance 在上述变换下按预期变化或保持不变，并且独立性保存。

## Theorem 4.2 起点：Brownian 路径的粗糙性

PDF 270 开始陈述 Theorem 4.2。其第 (a) 部分说：若 `0<a<1/2` 且 `T>0`，则对 Wiener measure 几乎处处的路径 p，

`sup_{0≤t≤T,0<h≤1}|p(t+h)-p(t)|/h^a < ∞`。

也就是说 Brownian 路径几乎处处具有任意指数严格小于 `1/2` 的局部 Hölder 控制。定理的 (b) 部分以及证明在 PDF 271 继续；本批不提前补写下一页内容。
