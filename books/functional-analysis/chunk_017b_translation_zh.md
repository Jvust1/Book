# chunk_017b 中文学习层（PDF 331-340 / 纸质 312-321）

> 原 PDF 为证据层；本文件是中文学习层。保留原书公式、定理、练习和问题编号，不把题解混入原题节点。

# Chapter 7 多复变函数初窥

## §8.2 Cauchy integral / Cauchy 积分（续）

由上一批定义的 `r(z,w)`，教材定义 Cauchy-Szegő 核

`S(z,w)=c_n r(z,w)^{-n}`, 其中 `c_n=(n-1)!/(4π)^n`。

它关于 `z` 全纯、关于 `w` 共轭全纯，并满足 `r(z,z)=Im(z_n)-|z′|^2=-ρ(z)`。公式 (37) 定义

`C(f)(z)=∫_{∂U}S(z,w)f(w)dβ(w)`。

**Theorem 8.5** 给出再生性质：若 `F∈H^2(U)`，`F_0` 是 Theorem 8.1 的 `L^2` 边界值，则 (38)

`C(F_0)(z)=F(z)`。

证明的关键是 **Lemma 8.6**。对固定 `λ>0`，在带高斯权 `e^{-4πλ|z′|^2}` 的整函数空间里，(39) 给出再生核

`K_λ(z′,w′)=(4λ)^{n-1}e^{4πλ z′·\bar w′}`。

再利用

`S(z,w)=∫_0^∞ λ^{n-1}e^{-4πλr(z,w)}dλ`

以及 §8.1 的 Fourier-Laplace 表示，把边界变量 `x_n` 的 Fourier 变换和 `z′` 方向的高斯再生核组合起来，就恢复 (33)，从而得到 Theorem 8.5。教材最后仍通过 `F^δ_ε` 先保证绝对收敛，再令 `δ→0`、`ε→0`。

## §8.3 Non-solvability / 不可解性

这里用 Cauchy 积分解释 Lewy 的经典局部不可解 PDE。对 `C^2` 上半空间边界，切向 Cauchy-Riemann 向量场采用教材给出的 Lewy 型约定。公式 (40) 把 `C(f)` 写成 `C×R` 上的积分，并进一步通过分布配对定义到紧支撑分布。

局部可解性的必要条件是 (41)：

`C(f)(z)` 必须能解析延拓到原点的某个邻域。

**Theorem 8.7**：若分布 `U` 在原点附近满足 `L(U)=f`，则 (41) 必须成立。证明先处理紧支撑情形，利用核在 `w` 变量的共轭全纯性得到 `C(f)=0`；一般局部情形再用 cutoff 把问题化到紧支撑情形。

教材最后构造一个在上半平面全纯、闭包上 `C∞`、快速衰减但不能穿过原点解析延拓的函数 `F(z_2)`，令 `f=F|_{∂U}`。Theorem 8.5 给出 `C(f)=F`，于是 (41) 失败，说明即使 `f` 是 `C∞`，Lewy 方程也可能在原点附近无局部解。

## §9 Exercises / 练习

本批完整收录 **Exercises 1-19**，每题均建立独立锚点。主题依次覆盖：多圆盘恒等定理；全纯域的对数凸性；一复变不可延拓函数；多复变零集触边；`\bar∂` 基本解卷积正则性；Cauchy-Green 公式；紧支撑 `\bar∂` 解的矩条件；定义函数与切向导数；Bochner 延拓的 Dirichlet 唯一性；连通性假设；collar 连通性；平面边界数据的矩条件；Levi 规范形；一复变边界正规化；不定 Levi 面上的全局延拓；`n=1` 时最大值原理失败；上半空间的 Heisenberg 对称；加权 Fock 空间 `H_λ`；以及 Cauchy 积分作为 `L^2` 正交投影。

## §10 Problems / 问题

本批完整收录 **Problems 1-6**：

1. 分别全纯在无连续性假设下推出联合全纯，并提示 Baire 纲定理的作用；
2. Weierstrass preparation theorem；
3. Bochner-Martinelli integral 对 Theorem 4.1 的原始证明；
4. 伪凸域上的 `\bar∂u=f`、normal solution 与 `\bar∂`-Neumann problem；
5. domain of holomorphy 与 pseudoconvexity；
6. Theorem 8.7 的逆命题，以及 Heisenberg 群卷积上的 relative inverse。

# Chapter 8 Fourier 分析中的振荡积分

PDF 340 正式进入第 8 章。开篇从 Fourier、Bessel 函数以及 Airy、Lipschitz、Stokes、Riemann 的早期渐近分析谈起，并指出 **stationary phase / 驻相原理** 是贯穿后续的核心思想；Kelvin 把这类方法用于水波，而数论中的格点问题又把振荡积分带入新的方向。

**这一章的历史导言在 PDF 340 尚未结束；PDF 341 将接着收尾并进入 §1 An illustration。**
