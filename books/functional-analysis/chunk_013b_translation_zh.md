# Functional Analysis 中文学习层：PDF 251-260（纸质页 232-241）

> 本批收尾 Chapter 5 的 Exercises / Problems，并正式进入 Chapter 6《An Introduction to Brownian Motion》。内容严格按教材顺序整理；Exercise 21(b) 从上一批续完，Chapter 6 §2 的技术预备在 PDF 260 起笔并跨到下一批。

## Chapter 5 Exercises 收尾

### Exercise 21(b)：q 进制正规数

设实数 α 的 q 进制展开数字为 `x_j∈{0,...,q-1}`，记 `#_{p,N}(α)` 为前 N 个位置中数字 p 出现的次数。若对每个 `0≤p≤q-1` 都有

`#_{p,N}(α)/N → 1/q`，

则称 α 对底数 q 是 normal。题目要求证明 `[0,1]` 中几乎所有实数都具有这一性质。教材 Hint 把 q 进制数字序列放到无限乘积 `∏Z_q` 上，并用均匀乘积测度与 Lebesgue 测度的对应，再调用 Theorem 2.1 的大数律。

### Exercises 22-35

22. 平稳过程：证明任一离散 stationary process 在联合分布意义下可写成某个 shift 系统 `{g_0(τ^n y)}`，因而遍历定理同样适用。
23. 证明 Theorem 2.1 中 `L1` 可积条件是尖锐的：若 iid 但 `∫|f_0|=∞`，则样本平均几乎处处不收敛；Hint 使用 Borel-Cantelli 型 Exercise 20。
24. 两个条件期望例子：有限/可数分割上的分块平均，以及乘积空间中积分掉第二个坐标。
25. 若 `s_n=E_n(s_∞)` 且 `s_∞∈L2`，则 martingale 在 `L2` 中收敛。
26. 建立条件期望的 `Lp` 收缩；反向证明 `1<p≤∞` 时一致 `Lp` 有界 martingale 有终值表示，并给出 `p=1` 失败例。
27. 对 `s_n=E_n(s_∞), s_∞∈L1`，证明 `L1` 收敛；并判别何时极限就是 `s_∞`：恰当且仅当 `s_∞` 对 `A_∞=∨A_n` 可测。
28. 建立终值版本的 martingale 最大不等式，并推出 `||sup_n|s_n|||_p≤A_p||s_∞||_p`。
29. 把前述 martingale 结果推广到 `R^d` 值情形。
30. 在 `R^d` 的 dyadic 立方体代数上定义条件期望，比较 `sup_n E_n f` 与 Hardy-Littlewood maximal function。
31. 证明概率测度弱收敛的多个等价刻画：特征函数、弱收敛、区间/开集概率收敛（在教材给定的连续性/绝对连续性条件下）。
32. 计算多维 Gaussian `ν_{σ²}` 的 Fourier 变换：`ν̂_{σ²}(ξ)=e^{-2π²|σξ|²}`。
33. 求 d 维随机游走 `s_n/√n` 的极限分布。
34. `d=1,2` 时证明随机游走几乎处处无穷多次访问任意固定格点。
35. `d≥3` 时证明 `|s_n|→∞` 几乎处处。

## Chapter 5 Problems

Problem 1 研究偏置 Bernoulli 测度在 `[0,1]` 上的 Riesz-product 型表示：由有限乘积构造分布函数 `F_N`，证明其单调、归一、均匀收敛，并在 `p≠1/2` 时得到完全奇异测度。

Problem 2* 讨论 lacunary Fourier 级数 `Σc_k e^{i2^kθ}` 与 Walsh-Paley/Rademacher 系的类比：`L2` 自动进入全部有限 `Lp`，而 `L∞` 恰对应 `Σ|c_k|<∞`。

Problem 3 给出一般的中心极限定理：独立但不必同分布，关键假设是教材写出的 Lindeberg 型尾部二阶矩条件。

Problem 4* 是 law of the iterated logarithm：对 iid、均值 0、方差 1 的和 `s_n`，教材给出

`limsup s_n/(2n log log n)^{1/2}=1` a.e.

Problem 5 研究“random flight”：每一步在单位球面上均匀选方向，要求用 Bessel 函数写出单步特征函数、求协方差，并给出 `s_n/√n` 的极限分布。

# Chapter 6 An Introduction to Brownian Motion / Brownian 运动导论

## 导论

教材把 Brownian motion 放在“随机性作为自然界内在不规则性”的背景下。选取的构造思路是：把上一章的格点 random walk 进行时间和空间缩放，考察连续插值路径诱导的概率测度是否收敛到路径空间上的 Wiener measure。

应用方向是 Dirichlet 问题。教材指出 Kakutani 的观点：对有界区域 `R⊂R^d`、内部点 x 和边界集合 `E⊂∂R`，从 x 出发的 Brownian path 首次离开 R 时落到 E 的概率就是关于 x 的 harmonic measure。后续需要 stopping time 与 strong Markov property。

## §1 The Framework / 框架

上一章随机游走为

`s_n(x)=Σ_{k=1}^n r_k(x)`。

对每个 N，把每一步时间缩为 `1/N`、空间缩为 `1/√N`，并在线性插值后定义式 (1)：

`S_t^(N)(x)=N^{-1/2}Σ_{1≤k≤[Nt]}r_k(x)+(Nt-[Nt])N^{-1/2}r_[Nt]+1(x)`。

教材先用式 (2) 非严格地写目标 `S_t^(N)→B_t`，随后明确真正要证明的是路径空间上的诱导测度弱收敛，而不是样本点上的几乎处处收敛。

### Brownian motion 的三条性质

令 `B_t` 取值于 `R^d`，并有 `B_0=0`。教材以三条性质刻画 Brownian motion：

- **B-1 独立增量**：`B_{t1}, B_{t2}-B_{t1}, ..., B_{tk}-B_{t{k-1}}` 相互独立。
- **B-2 Gaussian 增量**：`B_{t+h}-B_t` 为均值 0、协方差 `hI` 的 Gaussian。
- **B-3 连续路径**：几乎每个样本 `ω` 的路径 `t↦B_t(ω)` 连续。

因此 `B_t` 本身服从均值 0、协方差 `tI` 的正态分布。

### canonical path space 与 Wiener measure

定义路径空间

`P={p:[0,∞)→R^d : p 连续且 p(0)=0}`。

路径上的坐标过程为式 (3)：

`B~_t(p)=p(t)`。

若 `P` 上的概率测度 `W` 使这个坐标过程满足 B-1/B-2/B-3，则 W 称为 Wiener measure。教材强调：Wiener measure 的存在等价于 Brownian motion 的存在，后文还会证明唯一性。

### random-walk path measures 的真正极限目标

每个 `S_t^(N)(x)` 本身是一条 `P` 中的连续路径，因此原乘积测度 m 在 `P` 上诱导概率测度

`μ_N(A)=m({x:S_t^(N)(x)∈A})`。

本章的核心目标是

`μ_N ⇒ W`。

这就是随机游走缩放到 Brownian motion 的严格概率测度表述。

## §2 Technical Preliminaries 起点

PDF 260 开始给路径空间 P 配置一个刻画“紧区间上一致收敛”的度量。先定义

`d_n(p,p')=sup_{0≤t≤n}|p(t)-p'(t)|`，

再定义

`d(p,p')=Σ_{n=1}^∞ 2^{-n} d_n(p,p')/(1+d_n(p,p'))`。

其基本性质（收敛等价于紧集上一致收敛、完备性、可分性）从下一页继续，因此作为跨批次对象保留。
