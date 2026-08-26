# Functional Analysis 中文学习层：PDF 81–90（纸质页 62–71）

> 本批次完成 Hilbert 变换的 L^2 基础、M. Riesz 的 L^p 有界性定理及其证明主线，并进入极大函数与弱型估计。

# 3 Hilbert 变换的 L^p 理论

## 3.1 L^2 形式体系

### Cauchy 积分的 Fourier 表示

上半平面的 Cauchy 积分还可以写成

\[
F(z)=\int_0^\infty \widehat f(\xi)e^{2\pi iz\xi}\,d\xi,
\qquad \operatorname{Im}z>0.
\]

其关键基础恒等式是

\[
\int_0^\infty e^{2\pi iz\xi}\,d\xi=-\frac1{2\pi iz}.
\]

当 y→0 时，F(x+iy) 在 L^2 中趋向一个正频率投影 P(f)。P 是 L^2(R) 到“Fourier 变换在负频率一侧为零”的子空间上的正交投影。

### Hilbert 变换

教材据此定义

\[
H(f)(x)=\int_{-\infty}^{\infty}\widehat f(\xi)\frac{\operatorname{sign}(\xi)}{i}e^{2\pi ix\xi}\,d\xi.
\]

直接得到三条重要关系：

\[
P=\frac12(I+iH),\qquad \|Hf\|_2=\|f\|_2,\qquad H^2=-I.
\]

所以 H 在 L^2 上是酉算子，并且 \(H^{-1}=-H\)。

## 命题 3.1：奇异积分表示

Hilbert 变换也可以写成主值型奇异积分：

\[
H(f)(x)=\lim_{\varepsilon\to0}\frac1\pi\int_{|t|\ge\varepsilon}\frac{f(x-t)}{t}\,dt,
\]

其中极限在 L^2 范数中成立。

### Poisson 核与共轭 Poisson 核

教材定义

\[
P_y(x)=\frac{y}{\pi(x^2+y^2)},\qquad
Q_y(x)=\frac{x}{\pi(x^2+y^2)}.
\]

Cauchy 积分可写成

\[
F(x+iy)=\frac12\big[(f*P_y)(x)+i(f*Q_y)(x)\big].
\]

而它们的 Fourier 变换分别为

\[
\widehat{P_y}(\xi)=e^{-2\pi y|\xi|},\qquad
\widehat{Q_y}(\xi)=e^{-2\pi y|\xi|}\frac{\operatorname{sign}(\xi)}{i}.
\]

因此 \(f*Q_\varepsilon\to H(f)\)；教材再把截断奇异积分与 \(f*Q_\varepsilon\) 的差写成 \(f*\Delta_\varepsilon\)，并利用平移在 L^2 中的连续性与控制收敛证明该差趋于 0。

---

# 3.2 L^p 定理

## 定理 3.2（M. Riesz）

当 \(1<p<\infty\) 时，Hilbert 变换满足

\[
\|H(f)\|_{L^p}\le A_p\|f\|_{L^p}.
\]

它最初在 \(L^2\cap L^p\) 上定义，随后唯一连续延拓到全部 L^p。

## 为什么端点 p=1 与 p=∞ 失败？

教材用显式例子说明：

- 对 \(f=\chi_{(-1,1)}\)，H(f) 在 ±1 附近有对数奇点，且远处约按 1/x 衰减，所以不属于 L^1；
- 对另一个具有正负抵消的奇函数 g，H(g) 虽仍有对数奇点，但远处约按 1/x^2 衰减，因此可积。

PDF 84 的 **Figure 5** 已保留并视觉核对。它把两个原函数和各自 Hilbert 变换的图像并排展示，直观体现“是否具有总体抵消”对尾部衰减的影响。

教材随后指出：若 f 有界且紧支撑，则

\[
H(f)\in L^1(R)\quad\Longleftrightarrow\quad \int f=0.
\]

---

# 3.3 定理 3.2 的证明

证明先把问题归约到实值 \(C_0^\infty(R)\) 函数。对这类 f，其 Cauchy 积分延拓到闭上半平面并满足

\[
|F(z)|\le \frac{M}{1+|z|}.
\]

同时边界关系为

\[
2F(x)=f(x)+iH(f)(x).
\]

## Step 1：Cauchy 定理 + 偶整数指数

对整数 k≥2，利用上半平面中的大矩形积分路径得到

\[
\int_{-\infty}^{\infty}(F(x))^k\,dx=0.
\]

PDF 86 的 **Figure 6** 已保留并视觉核对，展示用于 Cauchy 定理的矩形路径 γ。

当 k=2 时，取实部恢复 H 在 L^2 上的酉性；当 k=2ℓ 为偶数时，展开 \((f+iHf)^{2\ell}\) 并使用 Hölder 不等式，可推出

\[
\|Hf\|_{L^p}\le A_p\|f\|_{L^p},\qquad p=2\ell.
\]

## Step 2：插值

已经知道 p=2 以及所有偶整数 p=2ℓ 的估计。用前一节的 Riesz 插值定理，在每个区间 [2,2ℓ] 内补齐全部中间指数，从而得到所有 \(2\le p<\infty\) 的有界性。

## Step 3：对偶

利用恒等式

\[
\int(Hf)g\,dx=-\int f(Hg)\,dx,
\]

若 1<p≤2，则其共轭指数 q≥2。把 q 上已经证明的 Hilbert 变换有界性通过上述对偶关系转移回 p，就得到整个范围 \(1<p<\infty\)。

这三步形成本定理的完整逻辑链：

**偶整数估计 → Riesz 插值补齐 p≥2 → 对偶得到 1<p≤2。**

---

# 4 极大函数与弱型估计

教材接下来引入极大函数

\[
f^*(x)=\sup_{x\in B}\frac1{m(B)}\int_B|f(y)|\,dy,
\]

其中上确界取遍所有包含 x 的球 B。它不是线性算子，但满足次可加性。

## 强 L^p 估计

目标是证明

\[
\|f^*\|_{L^p}\le A_p\|f\|_{L^p},\qquad 1<p\le\infty.
\]

p=∞ 显然成立，但 p=1 的强型估计失败。

## 弱 (1,1) 型替代

虽然 L^1→L^1 有界失败，教材给出替代估计：

\[
m\{x:f^*(x)>\alpha\}\le \frac{A}{\alpha}\|f\|_{L^1},
\qquad \alpha>0.
\]

其证明回顾 Vitali 覆盖思想：从高值集合的覆盖球中选取不交子族，再利用每个球上的平均值大于 α 来控制集合测度。

## 定理 4.1

若 \(f\in L^p(R^d)\)、\(1<p\le\infty\)，则 \(f^*\in L^p\) 且满足上述强 L^p 估计。

本批次在定理 4.1 的证明起点结束，下一批继续完成证明。

## 页码

- PDF：81–90
- 纸质正文：62–71
