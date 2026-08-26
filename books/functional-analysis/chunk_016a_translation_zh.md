# chunk_016a 中文学习层（PDF 301-310 / 纸质 282-291）

> 本文件是中文学习层；原 PDF 仍是证据层。公式编号、定理编号与图号均保持原书顺序。

# Chapter 7 A Glimpse into Several Complex Variables / 多复变函数初窥

## §2 Hartogs’ phenomenon: an example / Hartogs 现象（续）

Theorem 2.1 的证明从上一批继续。教材通过一列“阶梯”参数 `(α_k,β_k)` 与邻近的 `(a_k,b_k)`，反复使用 Lemma 2.2，把 F 的定义域逐步扩大：

`R_k = {ρ<|z|<1} ∪ {|z|<1; b_k≤|z_2|}`。

当迭代到 `a_N=1, b_N=0` 时，`R_N={|z|<1}`，于是球壳上的 F 已延拓到整个单位球。Figure 2 与 Figure 3 分别展示 `ρ<1/√2` 的几何情形与这一 staircase 推进。

一个直接后果是：当 `n>1` 时，`C^n` 中的 holomorphic function 不可能有孤立奇点，也不能有孤立零点。若 f 在 Ω 内某点为 0，则其零点集不能只停留在一个孤立点；更强地，零点集必须延伸到 Ω 的边界。

## §3 Hartogs’ theorem: the inhomogeneous Cauchy-Riemann equations

本节的核心方法是：先构造一个满足几何/边界要求但不一定全纯的近似函数，再通过解非齐次 `dbar` 方程消去其非全纯部分。

### 方程 (4)

`∂u/∂\bar z_j = f_j,  j=1,...,n`。

### 一维情形

方程 (5)：

`∂u/∂\bar z=f(z)`，其中

`∂/∂\bar z=(1/2)(∂/∂x+i∂/∂y)`。

显式解 (6) 为

`u(z)=(1/π)∫_C f(ζ)/(z-ζ) dm(ζ)=(1/π)∫_C f(z-ζ)/ζ dm(ζ)`。

也即 `u=f*Φ`，其中 `Φ(z)=1/(πz)`。

### Proposition 3.1

若 f 连续且紧支撑，则上述 u 连续，并在分布意义下满足 `dbar u=f`；若 `f∈C^k`，则 `u∈C^k` 且方程在通常意义下成立。反过来，任意紧支撑 `C^1` 函数 u 都满足

`u=(∂u/∂\bar z)*Φ`。

关键事实是 `Φ` 是 `∂/∂\bar z` 的基本解：

`∂Φ/∂\bar z=δ_0`。

### 高维相容条件 (7)

当 `n≥2` 时，给定的 `f_j` 不能任意选择，必须满足

`∂f_j/∂\bar z_k = ∂f_k/∂\bar z_j`。

### Proposition 3.2

若 `n≥2`，`f_j` 均为紧支撑 `C^k` 函数并满足上述相容条件，则存在紧支撑 `C^k` 函数 u，使

`∂u/∂\bar z_j=f_j`。

证明取 `z=(z',z_n)`，并定义 (8)

`u(z)=(1/π)∫_C f_n(z',z_n-ζ) dm(ζ)/ζ`。

利用相容条件与 Proposition 3.1 可依次得到所有 `∂u/∂\bar z_j=f_j`。紧支撑性来自：在外部区域 u 全纯且又在更远处为 0，于是由 identity principle 得到整个外部连通区域上 u=0。

这里出现一个重要维数差异：一维中，紧支撑 f 一般不能保证存在紧支撑 u；至少必须满足 `∫_C f dm=0`。但在 `n≥2` 时，Proposition 3.2 给出了紧支撑解，而且该紧支撑解是唯一的。

### Theorem 3.3：Hartogs 紧集挖洞延拓

设 `Ω⊂C^n` 有界、`n≥2`，`K⊂Ω` 紧，且 `Ω-K` 连通。则任意在 `Ω-K` 上解析的 `F_0` 都可解析延拓到整个 Ω。

证明机制：

1. 选 smooth cutoff `η`，在 K 邻域令 `η=0`，在靠近边界的区域令 `η=1`；
2. 定义一个光滑但不一定全纯的延拓 `F_1`；
3. 令 (9) `f_j=∂F_1/∂\bar z_j`；这些 `f_j` 在边界附近为 0，并可零延拓到整个 `C^n`；
4. 用 Proposition 3.2 解出紧支撑 u，使 `∂u/∂\bar z_j=f_j`；
5. 令 `F=F_1-u`，则 F 在 Ω 上全纯；
6. Figure 4 所示的边界小球中，u 因解析唯一性而消失，因此 F 与 `F_0` 在 `Ω-K` 的一个开集上相同，再由连通性与 identity principle 得到处处相同。

## §4 A boundary version: the tangential Cauchy-Riemann equations

本节开始研究极限情形：如果函数只给在边界 `∂Ω` 上，怎样判断它能否延拓为 Ω 内的 holomorphic function？

### 定义函数与 C^k 边界

区域 Ω 的 defining function `ρ` 满足：

- Ω 内 `ρ<0`；
- `∂Ω` 上 `ρ=0`；
- Ω 外 `ρ>0`。

若可取 `ρ∈C^k(R^d)` 且 `|∇ρ|>0` 于 `∂Ω`，称 `∂Ω` 为 `C^k` 边界。

由 implicit function theorem，在任意边界点附近，经平移和旋转可写成 (10)

`Ω: x_d>φ(x')`，
`∂Ω: x_d=φ(x')`。

Figure 5 展示了这一局部图表示。若 `\tildeρ` 是另一个定义函数，则局部有 (11)

`\tildeρ=cρ,  c(x)>0`。

### 切向向量场

实向量场 `X=Σ a_j(x)∂/∂x_j` 若满足 `X(ρ)=0` 于边界，则称 X tangential。由于两个 defining functions 只差一个正函数因子，这个定义与选取哪一个 ρ 无关。

边界函数 `f_0` 称为 `C^ℓ`，如果它有一个 `R^d` 上的 `C^ℓ` 延拓。对 tangential vector field X，`X(f)|_{∂Ω}` 与所选延拓无关。

### Cauchy-Riemann vector fields

在 `C^n` 中，一般复向量场可写成

`Σ [a_j(z)∂/∂\bar z_j + b_j(z)∂/∂z_j]`。

若所有 `b_j=0`，即

`X=Σ a_j(z)∂/∂\bar z_j`，

则称为 Cauchy-Riemann vector field；等价地，它消灭所有 holomorphic functions。

对区域 Ω，这样的 X 在边界切向当且仅当

`Σ a_j(z)ρ_j(z)=0`，其中 `ρ_j=∂ρ/∂\bar z_j`。

若局部 `ρ_n≠0`，则 (12)

`ρ_n ∂/∂\bar z_j - ρ_j ∂/∂\bar z_n,  1≤j≤n-1`

给出局部线性无关的切向 CR 向量场基。全局可用 (13)

`ρ_k ∂/∂\bar z_j - ρ_j ∂/∂\bar z_k,  1≤j<k≤n`

生成所有切向 CR 向量场，但它们一般不线性无关。

最后教材转入 differential forms 记号：

`\bar∂u=f`，其中

`\bar∂u=Σ (∂u/∂\bar z_j)d\bar z_j`。

对 `(0,1)`-form `w=Σw_jd\bar z_j`，定义 `(0,2)`-form `\bar∂w`。其展开式在 PDF 310 底部开始，**下一批 PDF 311 继续**。
