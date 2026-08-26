# chunk_016b 中文学习层（PDF 311-320 / 纸质 292-301）

> 本文件是中文学习层；原 PDF 仍是证据层。公式编号、定理编号与章节次序保持原书顺序。

# Chapter 7 A Glimpse into Several Complex Variables / 多复变函数初窥

## §4 A boundary version: the tangential Cauchy-Riemann equations / 边界版切向 Cauchy-Riemann 方程（续）

上一批在 differential forms 记号处结束。若

`w=Σ_j w_j d\bar z_j`

是一个 `(0,1)`-form，则

`\bar∂w = Σ_{k<j}(∂w_j/∂\bar z_k − ∂w_k/∂\bar z_j)d\bar z_k∧d\bar z_j`。

因此非齐次 Cauchy-Riemann 系统可简写为 `\bar∂u=f`，其相容条件就是 `\bar∂f=0`。

边界函数 `F_0` 被所有切向 Cauchy-Riemann 向量场消去，当且仅当公式 (14) 成立：

`\bar∂F_0 ∧ \bar∂ρ |_{∂Ω}=0`。

这说明：若 `F_0` 真的是 Ω 内全纯函数在边界上的限制，那么它必然满足切向 CR 方程。Bochner 定理表明，在适当全局条件下，反过来也基本成立。

### Theorem 4.1 / Bochner theorem

设 Ω 是 `C^n` 中有界区域，`∂Ω` 为 `C^3`，且补集 `Ω^c` 连通。若 `F_0∈C^3(∂Ω)` 满足切向 Cauchy-Riemann 方程，则存在 Ω 内全纯、在闭包上连续的 F，使 `F|_{∂Ω}=F_0`。

证明先把 `F_0` 修改为 `F_1=F_0-aρ`，使公式 (15)

`\bar∂F_1|_{∂Ω}=0`

成立。用于确定 a 的非切向 CR 向量场为

`N(f)=Σ \overline{ρ_j} ∂f/∂\bar z_j`，

而

`N(ρ)=Σ|∂ρ/∂z_j|²=(1/4)|∇ρ|²>0`。

因此在边界附近可取 `a=N(F_0)/N(ρ)`。随后令 `f=\bar∂F_1`，在 Ω 外零延拓。因为 `f` 满足 `\bar∂f=0`，可用 Proposition 3.2 解出紧支撑 u，使 `\bar∂u=f`。由于 `u` 在连通的 `Ω^c` 上全纯且在无穷远处为 0，故 `u=0` 于 `Ω^c`。最后取

`F=F_1-u`，

就得到所需全纯延拓。

## §5 The Levi form / Levi 形式

实变量中，局部边界可通过任意光滑坐标改变压平为半空间；但在复分析中只能允许 holomorphic coordinate changes，因此会保留一个二阶不变量——Levi form。

### Proposition 5.1

在任意边界点 `z_0∈∂Ω` 附近，可取以 `z_0` 为中心的全纯坐标，使 Ω 具有规范形式 (16)：

`Im(z_n) > Σ_{j=1}^{n−1} λ_j|z_j|² + E(z)`，

其中 `λ_j∈R`，而

`E(z)=x_nℓ(z′)+Dx_n²+o(|z|²)`。

通过进一步缩放，可把非零的 `λ_j` 归一成 `±1`。正、负、零特征值的个数（signature）是 holomorphic invariant。

证明通过 Taylor 展开去掉纯 `z_jz_k` 二次项，再用 unitary transformation 对 Hermitian 二次型对角化，得到公式 (17)：

`φ=Σ λ_j|z_j|²+x_nℓ(z′)+Dx_n²+o(|z|²)`。

### Levi form

Levi form 在这些坐标里就是 Hermitian 二次型 `Σ λ_j|z_j|²`。内在地，它可写成公式 (18)：

`Σ (∂²ρ/∂z_j∂\bar z_k)a_j\bar a_k`，

并限制在 complex tangent vectors 上。

若换 defining function `ρ′=cρ`（`c>0`），或做 biholomorphic coordinate change，Levi form 的 signature 不变。

- Levi form 非负：该边界点称为 **pseudo-convex / 伪凸**；
- Levi form 正定：称为 **strongly pseudo-convex / 强伪凸**。

单位球取 `ρ(z)=|z|²−1` 时，Levi form 是恒等型，所以单位球处处强伪凸。

## §6 A maximum principle / 极大值原理

若边界的 Levi form 至少有一个严格正特征值，就得到一个在一维复分析中不存在对应物的局部极大值原理。

### Theorem 6.1

设 Ω 有 `C²` 边界，B 是以 `z_0∈∂Ω` 为中心的球；若 `∂Ω∩B` 上每一点的 Levi form 至少有一个严格正特征值，则存在更小的球 `B′⊂B`，使

(19) `sup_{Ω∩B′}|F| ≤ sup_{∂Ω∩B}|F|`

对所有在 `Ω∩B` 上全纯并连续到相关边界的 F 成立。

证明先在 Proposition 5.1 的规范坐标中考察一维复切片，只允许 `z_1` 变化。对点 `(0,0,iy_n)` 得到预备估计 (20)：

`|F(0,0,iy_n)| ≤ sup_{∂Ω∩B_r}|F|`。

核心几何事实 (21) 是：切片区域 `Ω_1` 的边界点不会来自球面 `∂B_r`，而必须落在 `∂Ω` 上。于是普通的一维 maximum principle 可以应用。

再对一般靠近边界的 z，取唯一最近边界点 `π(z)`，并在 `π(z)` 处选规范坐标；由于 `z-π(z)` 垂直于切平面，z 在新坐标中正好变成 `(0,0,iy_n)`，从而把一般情形归约到上述切片估计。

### Corollary 6.2

同样的结论适用于局部 `C²` hypersurface M。若 Levi form 在 M 的每点至少有一个严格正特征值，则局部有

(22) `sup_{Ω^-∩B′}|F| ≤ sup_M |F|`。

这为下一节的局部 Bochner 延拓提供了“边界控制内部”的关键工具。

## §7 Approximation and extension theorems / 逼近与延拓定理

教材把经典 Weierstrass approximation 推广到 `C^n` 中的局部 hypersurface。目标是：给定 M 上的连续 F，何时可以由 holomorphic polynomials 在 M 上局部一致逼近？

将局部超曲面写为 (23)：

`M={z=(z′,z_n): Im(z_n)=φ(z′,x_n)}`。

相应切向 Cauchy-Riemann 算子可写成 (24)：

`L_j(f)=∂f/∂\bar z_j − a_j ∂f/∂\bar z_n`，

其中 `a_j=ρ_j/ρ_n`。

通过定义转置算子 `L_j^t` 并积分分部，教材把 tangential CR equations 扩展到连续函数：若对所有支撑足够小的 `C¹` 测试函数 ψ 都有

`∫ f L_j^t(ψ)=0`，

则称 f 在 **weak sense / 弱意义** 下满足切向 CR 方程。

### Theorem 7.1 / Baouendi-Treves approximation theorem

若 `M⊂C^n` 是 `C²` hypersurface，则在任意 `z_0∈M` 附近存在 `B′⊂B`，使得每个在 `M∩B` 上连续、并在弱意义下满足 tangential CR equations 的 F，都能在 `M∩B′` 上被变量 `z_1,...,z_n` 的 holomorphic polynomials 一致逼近。

证明从 PDF 320 开始。教材先固定 `u∈R^{n−1}`，把 M 分解成切片

`M_u={z: y_n=φ(z′,x_n), z′=x′+iu}`，

并用

`Φ_u(x)=(x′+iu, x_n+iφ(x′+iu,x_n))`

参数化每个 `M_u`。其 Jacobian 矩阵是 `I+A(x)`，且

`det(∂Φ/∂x)=1+iφ_{x_n}`。

这诱导出切片上的复密度测度 `dm_u=J(x)dx`。**Theorem 7.1 的证明在下一批 PDF 321 继续。**
