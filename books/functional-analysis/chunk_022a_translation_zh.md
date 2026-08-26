# chunk_022a 中文学习层

范围：PDF 421-430 / 纸质页 402-411。

## Chapter 8 - §9 Exercises 收尾

### Exercise 16
这是 Proposition 6.6 与 6.8 的逆向刻画。若 $u(\cdot,t)$ 对每个 $t$ 都在 $L^2(\mathbb R^d)$ 中，且随 $t$ 在 $L^2$ 范数下连续，$u(\cdot,0)=0$，并满足
$$
\frac1i\frac{\partial u}{\partial t}-\Delta u=F
$$
（分布意义），其中 $F\in L^2(\mathbb R^d\times\mathbb R)$，则要证明 $u=S(F)$。教材提示把差 $u-S(F)$ 变到 interaction picture：$e^{-it\Delta}(u-S(F))$，再用“时间导数为 0 且初值为 0 的 $L^2$-连续函数恒为 0”。

### Exercise 17
讨论临界非线性 Schrödinger 方程的两个适定性性质：**唯一性**和**对初值的连续依赖**。参数为 $\lambda=(d+4)/d$、$q=(2d+4)/d$。证明仍沿用 Theorem 6.9 的压缩映射估计：先在足够短的时间区间上使两个解的 $L^q$ 范数都小于阈值，再逐段平移时间区间得到全局于给定存在区间的唯一性；对邻近初值则得到局部 Lipschitz 型估计。

### Exercises 18-20：Radon 变换与解析插值
- **Exercise 18**：奇维非退化双线性 Radon 变换 $R_B$。先得到 $x_d$ 方向的 $(d-1)/2$ 阶 $L^2$ 恒等式，再识别形式伴随，最后得到反演公式
  $$
  \left(i\frac{\partial}{\partial x_d}\right)^{d-1}R_B^*R_B(f)=c_Bf.
  $$
- **Exercise 19**：对局部化算子 $R'_B=\eta'R_B(\eta f)$，证明 $L^2$ 有界性，并把一般导数化为有限个 $x_d$ 导数型项，从 Exercise 18 推出 $L^2\to L^2_{(d-1)/2}$ 平滑。
- **Exercise 20**：令
  $$
  T_s=(1-2^{1-s})e^{s^2}\sum_{k=0}^r2^{-ks}A_k.
  $$
  在 $\Re s=-(d-1)/2$ 上做 $L^2$ 估计，在 $\Re s=1$ 上做 $L^1\to L^\infty$ 估计，再用 Proposition 4.4 插值得到 $p=(d+1)/d, q=d+1$ 的平均算子估计。

### Exercises 21-23
- **Exercise 21**：凸域的几何膨胀性质：$x\in R\Omega$ 且 $|y|\le\delta$ 时，$x+y\in(R+c\delta)\Omega$。提示先缩放到 $R=1$，再用边界局部图和凸性。
- **Exercise 22**：加权除数函数和：$\alpha>-1$ 时前缀和为 $O(r^{\alpha+1}\log r)$；$\alpha<-1$ 时尾和也是同一量级。
- **Exercise 23**：由 Bessel 递推关系得到
  $$rJ_1(r)=\int_0^r\sigma J_0(\sigma)\,d\sigma.$$

## Chapter 8 - §10 Problems

这些问题不是常规练习，而是进一步结果的路线图。

1. **Gauss map 与曲率**：非零 Gauss 曲率等价于 Gauss map 局部为微分同胚，并有 $K\,d\sigma_M=(d\sigma_{S^{d-1}})^*$。
2. **Spherical maximal function**：$p>d/(d-1)$ 时球面极大算子在 $L^p$ 上有界；教材给出 $d\ge3,p=2$ 的局部提示。
3. **Wave equation 初值恢复**：在 $p>2d/(d+1)$ 时，$u(x,t)/t\to f(x)$ 几乎处处。
4. **二维 restriction**：在 $\mathbb R^2$ 中达到 $1\le p<4/3$ 的完整范围，核心是 $\nu*\nu$ 的绝对连续性与 Hausdorff-Young。
5. **Wave Strichartz**：$d\ge3$ 时对应的时空指数为 $q=(2d+2)/(d-2)$。
6. **Gauss circle error**：记录 Hardy 级数、均方渐近、$R^{1/2}$ 归一化的无界 limsup，以及改进指数 $\alpha=131/208$。
7. **Bessel 型表示**：
   $$J(\lambda)=4K_0(2\lambda)-2\pi Y_0(2\lambda).$$
8. **Divisor problem error**：$\Delta(\mu)$ 可写成包含 $K_1,Y_1$ 的 Voronoi 型收敛级数，且相应误差指数满足 $\beta=\alpha/2$。

## Notes and References

PDF 428 起进入书后 **Notes and References**。这一部分不是新增数学定理，而是给正文中的引语、定理、练习和 Problems 指明文献来源。

- **Chapter 1**：Riesz、Banach 引语；Banach 空间的一般来源；Clarkson 不等式、Orlicz 空间等。
- **Chapter 2**：Young、M. Riesz/Hardy 书信；共轭函数、$H^1_r$、BMO 与相关问题的参考。
- **Chapter 3**：Schwartz 分布理论、Gelfand-Shilov，以及更一般的核/乘子结果。
- **Chapter 4**：Baire 原始文献、Besicovitch 集、universal element 与 hypercyclic operator。
- **Chapter 5**：Kolmogorov/Kac 引文；概率论、随机过程、Walsh-Paley 与 lacunary series。
- **Chapter 6**：Brownian motion 的一般参考与相关 Problems 的来源。
- **Chapter 7**：Lewy、若干复变、Baouendi-Treves 逼近、CR 理论、上半空间与 Heisenberg group。
- **Chapter 8**：Kelvin/Stokes 引文；振荡积分、restriction、色散方程、格点计数，以及各 starred Problems 的进一步文献，包括 Huxley 的 $131/208$ 指数和 Voronoi 恒等式。

PDF 430 结束 Notes and References。PDF 431 是原书刻意留白页，Bibliography 从 PDF 432 / 纸质页 413 开始。
