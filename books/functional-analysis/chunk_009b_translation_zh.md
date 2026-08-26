# Functional Analysis 中文学习层：PDF 171-180（纸质页 152-161）

> 本批次收尾第 3 章，并正式进入第 4 章 Baire 纲定理。原文、公式与题号作为证据层保留；本文件是便于预习/学习/复习的中文学习层。

## Chapter 3：Exercises 29-34 收尾

### Exercise 29：Sobolev 嵌入提示
上一批建立了 `H^m(R^d)` 的 Fourier 刻画。本页提示指出：当 `|α| < m-d/2` 时，`ξ^α f̂ ∈ L^1`，因此可由 Fourier 反演得到相应导数的连续性。这给出 `m>d/2` 时的连续代表，以及更高阶 `C^k` 正则性。

### Exercises 30-34
- **30**：临界齐次核 `1/|x|^d` 的 Fourier 变换出现 `log|ξ|`，说明球面平均不为零时无法得到有界 Fourier 乘子，因此不能在 `L^2` 上有界。
- **31**：球面平均为零的齐次 `-d` 次核主值分布是 Calderón-Zygmund 分布，但对应算子一般仍不在端点 `L^1`、`L^∞` 上有界。
- **32**：证明定义 CZ 分布时较高阶的 bump cancellation 条件实际上蕴含 `C^(1)` 版本。
- **33**：给出 CZ 分布存在性的环带积分判据：`sup_{0<a<b}|∫_{a<|x|<b}k|<∞`。
- **34**：验证 Schwartz 函数与 CZ 分布相乘仍保持 CZ 性质。

## Chapter 3：Problems 1-8

1. **周期分布与 Fourier 级数**：把“R^d 上 Z^d-周期分布”和“`D(T^d)` 上连续线性泛函”对应起来；周期分布的 Fourier 系数只需缓增，Fourier 级数在分布意义下收敛。
2. **CZ 算子作用于 H^1_r**：利用原子分解证明奇异积分在实 Hardy 空间上有界，因此特别映入 `L^1`。
3. **椭圆算子的内部 L^p-Sobolev 估计**：使用小支撑 parametrix、截断函数和 Theorem 3.2，把定性的椭圆正则性升级为定量估计。
4*. **振荡奇异积分**：`pv(e^{iP(x)}k(x))` 的 Fourier 变换有界，而且界与多项式 P 的系数无关。
5*. **多项式幂的亚纯延拓**：研究 `I(s)(φ)=∫_{Q>0}|Q|^s φ` 的全平面亚纯延拓及极点结构。
6*. **一般常系数 PDE 的基本解**：由 Problem 5 推出任意非零常系数微分算子都有 tempered fundamental solution。
7*. **hypo-elliptic 判据**：用特征多项式 P 的导数比值 `∂^αP/P→0` 刻画 hypo-ellipticity。
8*. **波动算子的多个基本解**：构造前向 `F+`、后向 `F-` 与 Fourier 侧定义的 `F0`，比较其锥支撑、齐次性、Lorentz 不变性与 Huygens 原理。

至此第 3 章正文、Exercises 和 Problems 均已完成结构化。

## Chapter 4：Baire 纲定理的应用

本章的主线不是“再造一个反例”，而是用 Baire category 说明很多看似反常的现象其实是 **generic（典型）** 的：逐点极限的连续性、处处不可微连续函数、Fourier 级数发散，以及开映射/闭图定理等。

### 1 Baire category theorem：基本概念

建立以下拓扑概念：
- interior / closure：内部与闭包；
- dense：稠密；
- nowhere dense：无处稠密；
- first category / meager：第一纲，即可数个无处稠密集的并；
- second category：不是第一纲；
- generic：补集是第一纲。

特别注意：**category 与 Lebesgue measure 没有直接对应关系**。第一纲集可以有满测度，generic 集也可以是零测度。

### Theorem 1.1：Baire 纲定理

> 每个完备度量空间在自身中是第二纲的；等价地，它不能写成可数个无处稠密集的并。

证明核心是嵌套闭球：依次选择 `B_n` 避开 `F_n`，令半径趋于 0。任取 `x_n∈B_n` 得到 Cauchy 列；完备性给出极限 x，而 x 同时避开所有 `F_n`，与覆盖假设矛盾。

### Corollary 1.2
在完备度量空间中，generic 集必稠密。

### 1.1 连续函数列的逐点极限

Theorem 1.3 开始：若连续函数 `f_n` 在完备度量空间 X 上逐点收敛到 f，则 f 的连续点集合是 generic 的。

关键工具是振荡：
`osc(f)(x)=lim_{r→0} sup_{y,z∈B_r(x)}|f(y)-f(z)|`。

`osc(f)(x)=0` 当且仅当 f 在 x 连续。Lemma 1.4 利用 Baire 定理，从逐点收敛中抽出一个小球，在该小球上某个 `f_m` 对 f 一致接近；证明将在下一批完成。
