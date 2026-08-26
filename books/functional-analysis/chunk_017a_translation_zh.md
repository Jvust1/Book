# chunk_017a 中文学习层（PDF 321-330 / 纸质 302-311）

> 原 PDF 为证据层；本文件是中文学习层，保留原书公式、定理和章节编号。

# Chapter 7 多复变函数初窥

## §7 逼近与延拓定理（续）

Baouendi-Treves 定理的证明从切片 `M_u` 上的高斯型核开始。定义公式 (25)

`F^u_ε(ζ)=ε^{-n/2}∫_{M_u} exp[-π(z−ζ)^2/ε]F(z)χ(z)dm_u(z)`。

证明需要三点：它对 ζ 是 entire；在同一切片内收敛到 F；不同切片间 `F^u_ε−F^0_ε→0`。公式 (26) `Re(z−ζ)^2≥c|x−ξ|^2` 提供指数衰减。Lemma 7.2 / (27) 给出复矩阵高斯积分恒等式，Corollary 7.3 将其解释为 approximation to the identity。

Lemma 7.4 / (28) 是证明的关键微分恒等式：

`∂_{u_j}∫_{M_u}f dm_u=(2/i)∫_{M_u}L_j(f)dm_u`。

借此得到不同切片间的公式 (29)。对只连续、弱意义满足 CR 方程的 F，再通过 (30)、(31) 和两组逼近恒等核恢复 (29)，于是完成 Theorem 7.1。

### Theorem 7.5 / Lewy extension theorem

若 M 上 Levi form 每点至少有一个严格正特征值，则连续弱 CR 边界函数可局部延拓到负侧 `Ω^-` 内的全纯函数。证明把 Theorem 7.1 的多项式逼近与 §6 的局部极大值原理直接拼接。

## §8 Appendix: The upper half-space / 上半空间附录

模型区域

`U={z∈C^n: Im(z_n)>|z′|^2}`，

边界由 (32) `Im(z_n)=|z′|^2` 给出。它通过分式线性变换与单位球双全纯等价。边界用 `(z′,x_n)` 参数化，并以 Lebesgue measure 作为自然测度 `dβ`。

### §8.1 Hardy space

`H^2(U)` 由

`sup_{ε>0}∫_{∂U}|F(z′,z_n+iε)|^2dβ<∞`

定义。Theorem 8.1 说明 `F_ε` 在 `L^2(∂U)` 中收敛到边界值 `F_0`，且范数相等。Lemma 8.2 用均值性质给出全纯函数的局部 `L^2→L^∞` 控制。

教材引入加权 Hilbert 空间 H，并得到 Fourier-Laplace 表示 (33)

`F(z′,z_n)=∫_0^∞f(z′,λ)e^{2πiλz_n}dλ`。

Proposition 8.3 证明 H 与 `H^2(U)` 之间的表示是双向的，并由 (34) 得到

`||F_0||_{L^2(∂U)}=||F||_{H^2(U)}=||f||_H`。

在边界参数化后，切向 CR 向量场为

`L_j=∂/∂\bar z_j−iz_j∂/∂x_n`。

公式 (35) 给出弱 CR 条件。Proposition 8.4 表明：`F_0∈L^2(∂U)` 是某个 `H^2(U)` 函数的边界值，当且仅当 `F_0^#` 弱意义满足这些切向 CR 方程。其逆向证明用 (36) 的 x_n 部分 Fourier 变换，并证明负频率部分必须消失。

### §8.2 Cauchy integral（起点）

PDF 330 开始定义 Cauchy-Szegő integral 的基本函数

`r(z,w)=(i/2)(\bar w_n−z_n)−z′·\bar w′`。

**核的进一步构造从 PDF 331 继续。**
