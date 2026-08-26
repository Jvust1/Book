# chunk_015b 中文学习层（PDF 291-300 / 纸质 272-281）

> 本文件是中文学习层；原 PDF 仍是证据层。定理、公式、习题与问题编号均保持原书顺序。

# Chapter 6 An Introduction to Brownian Motion

## §7 Exercises / 习题 15-21

15. 计算 Brownian motion 在多个时刻 `(B_{t1},...,B_{tk})` 的联合概率分布。
16. 令 `A_{t+}=∩_{s>t}A_s`，证明 Brownian filtration 的右连续性 `A_{t+}=A_t`。
17. 对每个 `t>0`，证明 `A_t=A_{t-}`，其中 `A_{t-}` 由所有 `s<t` 的 `A_s` 生成。
18. 对 stopping time `σ`，证明 `σ` 与 `B_σ` 都是 `A_σ`-measurable，并证明 `A_σ` 正是 stopped process `B̂_t=B_{t∧σ}` 所决定的 σ-algebra。
19. 若有界 Borel 函数 u 满足球面平均值性质，则先推出球平均公式，再得到连续性与调和性。
20. 证明 Lipschitz boundary 蕴含 outside cone condition；因此 `C^1` 区域也满足该条件，Dirichlet 问题可唯一求解。
21. 对嵌套区域 `R1⊂R2`，证明 harmonic measure 的复合关系

`μ_2^x = ∫_{∂R1} μ_2^y dμ_1^x`。

## §8 Problems / 问题 1-7

1. 给出 Kolmogorov continuity theorem 型结果：若 `||F_{t1}-F_{t2}||_p≤c|t1-t2|^α` 且 `α>1/p`，则存在修正版 `F̃_t`，其样本路径几乎处处连续，并具有任意 `γ<α-1/p` 阶的 Hölder 正则性。
2. 把 Donsker invariance principle 推广到一般独立同分布、均值 0、协方差为单位矩阵的 `R^d` 值增量。
3. 用 Hilbert 空间同构 `U:L^2([0,∞))→H` 与 `B_t=U(χ_[0,t])` 构造 Brownian motion。
4. 证明 Brownian motion 的维数依赖：`d=1` 点常返；`d≥2` 几乎不命中固定点；`d=2` 对每个邻域常返；`d≥3` 暂留并逃向无穷远。
5. 写出 Brownian motion 在 `t→∞` 与经 time inversion 后 `t→0` 的 law of the iterated logarithm。
6. `d≥2` 时证明 Theorem 6.1 的逆命题：若每个连续边界数据都在 y 处连续取到边值，则 y 必为 regular point。
7. Lebesgue thorn：从球中挖去尖刺集合 E；当 f 在 0 附近衰减足够快时，原点成为非正则边界点。

# Chapter 7 A Glimpse into Several Complex Variables / 多复变函数初窥

本章强调：进入多复变后，会出现一元复分析中没有的现象，包括某些区域上的**自动解析延拓**、切向 Cauchy-Riemann 算子的关键作用，以及边界的复凸性。

## §1 Elementary properties / 基本性质

对 `z0∈C^n` 与 `r=(r1,...,rn)`，定义 polydisc

`P_r(z0)={z: |z_j-z_j^0|<r_j}`

以及对应的边界圆周乘积

`C_r(z0)={z: |z_j-z_j^0|=r_j}`。

教材列出连续函数 f 在开集 Ω 上“全纯”的四个等价刻画：

1. 分布意义下满足 Cauchy-Riemann 方程 `∂f/∂\bar z_j=0`；
2. 固定其余变量后，对每一个单独的复变量都解析；
3. 在每个闭包含于 Ω 的 polydisc 上满足多变量 Cauchy 积分公式；
4. 每点附近都有绝对且一致收敛的幂级数展开。

### Proposition 1.1

上述四个条件等价。证明链为 `(i)⇒(ii)⇒(iii)⇒(iv)⇒(i)`：

- `(i)⇒(ii)`：由 `Δ=4∑ ∂/∂z_j · ∂/∂\bar z_j` 得 `Δf=0`，再用 Chapter 3 的 elliptic regularity 得 `f∈C^∞`；
- `(ii)⇒(iii)`：依次对每个变量使用一元 Cauchy integral formula；
- `(iii)⇒(iv)`：对每个 `1/(ζ_k-z_k)` 作几何级数展开；
- `(iv)⇒(i)`：在较小 polydisc 内逐项求导。

幂级数系数满足

`a_α=(2πi)^(-n) ∫_{C_r(z0)} f(ζ) ∏ dζ_k/(ζ_k-z_k)^(α_k+1)`，

并有 `|a_α|≤M r^{-α}`。

教材随后指出：若 f 仅 locally integrable、且分布意义下满足 Cauchy-Riemann 方程，也可在零测集上修正后成为连续全纯函数。

### Proposition 1.2：解析恒等定理

若区域 Ω 上的两个 holomorphic functions 在某点邻域内相同，则它们在整个 Ω 上相同。证明利用 Ω 的 pathwise connectedness 与一串相互重叠的 polydiscs 把局部零集向目标点传播。

## §2 Hartogs’ phenomenon: an example / Hartogs 现象：一个例子

### Theorem 2.1

若 `n≥2`，并且 F 在球壳

`Ω={z∈C^n: ρ<|z|<1}`

上 holomorphic，则 F 可以解析延拓到整个单位球。

教材先在 `C^2` 中建立一个基本延拓构造。定义

`K1={|z1|≤a, |z2|=b1}`，
`K2={|z1|=a, b2≤|z2|≤b1}`。

### Lemma 2.2

若 F 在包含 `K1∪K2` 的区域 O 上 holomorphic，则 F 可延拓到某个开集 `Õ`，且 `Õ` 包含乘积区域

`{|z1|≤a, b2≤|z2|≤b1}`。

Figure 1 给出了这一阴影乘积区域。证明使用

`I(z1,z2)=(1/(2πi))∫_{|ζ1|=a+ε} F(ζ1,z2)/(ζ1-z1)dζ1`。

Theorem 2.1 的证明已在 PDF 300 开始，并将在下一批继续。
