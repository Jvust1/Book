# chunk_015a 中文学习层（PDF 281-290 / 纸质 262-271）

> 本文件是中文学习层；原 PDF 仍是证据层。定理、公式、习题编号与页码均保持原书顺序。

# Chapter 6 An Introduction to Brownian Motion

## §5.3 Other forms of the strong Markov Property / 强 Markov 性质的其他形式

### Theorem 5.5：两个停止时刻与 stopped process

设 `σ≤τ` 都是 stopping times，并把从位置 y 出发、在退出 R 的时刻 `τ_y` 停止的过程记为 `B̂_t^y`。Theorem 5.5 的式 (19)说明：从随机时刻 σ 之后继续观察到时间 t，并在 τ 处停止，与“先读取 σ 时刻的位置 y，再从 y 启动一条独立 Brownian path 并按同一退出规则停止”具有相同的积分分布。

证明把左端拆成 `τ≥σ+t` 与 `τ<σ+t` 两种情形，分别利用 Theorem 5.4 的路径函数强 Markov 形式，最后合并为式 (19)。教材最后说明，同样的恒等式可在任意 `A∈A_σ` 上积分，因此得到相对于 `A_σ` 的 conditional expectation 版本。

## §6 Solution of the Dirichlet problem / Dirichlet 问题的解

对有界开集 `R⊂R^d` 和边界连续函数 f，令 `μ_x` 是从 x 出发的 Brownian motion 第一次离开 R 时在 `∂R` 上的退出分布。定义

`u(x)=∫_{∂R} f(y)dμ_x(y)`  （20）

### Theorem 6.1

1. `u` 在 R 内 harmonic；
2. 若 `y∈∂R` 是 regular boundary point，则当 `x→y` 且 `x∈R` 时，`u(x)→f(y)`。

证明 (a) 固定 x，在 R 内取以 x 为中心的球面 S。Brownian motion 从 x 首次到达 S 的分布由旋转不变性得到为均匀球面测度，因此得到平均值性质

`u(x)=∫_S u(y)dm(y)`  （21）。

Figure 2 直观展示了路径先在 S 的 stopping time σ 处停止，再继续直到 `∂R` 的退出时刻 τ。强 Markov 性质把“从 x 直接退出 R”与“先到 S，再从随机命中点继续退出 R”连接起来，得到式 (23)，从而证明平均值性质。

证明 (b) 先由 regularity 得到对每个 `δ>0`，`P(τ_x>δ)→0`（24）。结合 Brownian maximal inequality，进一步得到退出位置集中在 y 附近（25）。再把边界积分分成 y 的小邻域和其补集，利用 f 的连续性完成极限。

### Proposition 6.2：outside cone regularity

截断锥定义为

`Γ={z: |z|<α(z·γ), |z|<δ}`，其中 `α>1`。

若 `x∈∂R` 且存在某个截断锥 Γ，使 `x+Γ` 与 R 不相交，则 x 是 regular boundary point。证明用 Blumenthal zero-one law 与 Brownian motion 的旋转不变性：路径几乎必然在任意小时间内进入某个这样的锥形方向。

Figure 3 给出 boundary point x 处的 outside truncated cone。由此定义 **outside cone condition**：每个边界点都存在这样的外锥。

### Corollary 6.3

若有界开集 R 满足 outside cone condition，则对每个连续边界数据 f，都存在唯一函数 u，使得 u 在闭包上连续、在 R 内 harmonic，并满足 `u|_{∂R}=f`。存在性由 Theorem 6.1 + Proposition 6.2 得到，唯一性来自 maximum principle。

## §7 Exercises / 习题 1-14

1. 证明缩放随机游走的单时刻与增量分布弱收敛到相应 Gaussian law。
2. 验证路径空间 `(P,d)` 完备且可分。
3. 用 Baire category theorem 证明 P 不是 σ-compact。
4. 证明紧致度量空间 X 与 `C(X)` 都可分。
5. 把紧集 K 上的连续函数等 sup 范数延拓到整个度量空间 X。
6. 对紧路径族建立统一的时间增量模 `w_T(h)→0`。
7. 从弱收敛推出开集上的 Portmanteau 型 liminf 与边界零测时的收敛。
8. 说明 canonical Wiener measure 与任意满足 B-1/B-2/B-3 的 Brownian realization 之间的对应。
9. 构造 strict Brownian process，并证明 strict realization 在忽略零测集后本质唯一。
10. 推广 Khinchin inequality 到有界、独立同分布、均值为 0 的 `R^d` 值随机变量。
11. 对独立同分布部分和最大值建立任意阶 `O(λ^{-p})` 尾界。
12. 证明几乎处处 `|B_t|=O(t^{1/2+ε})`（`t→∞`）。
13. 证明时间反演过程 `B'_t=tB_{1/t}` 仍是 Brownian motion。
14. 证明几乎处处 Brownian 路径在 0 附近不是 Hölder `1/2`，并且在无穷远最终离开任意固定球。
