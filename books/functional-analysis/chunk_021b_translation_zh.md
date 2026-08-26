# chunk_021b 中文学习层（PDF 411-420 / 纸质 392-401）

## Chapter 8 §8.4 Fourier 变换收尾（PDF 411）

### Theorem 8.9 完成

PDF 410 已把截断函数 `f_epsilon` 写成双曲坐标积分并得到公式 (93)。PDF 411 指出其余三个象限完全类似，再沿用 Proposition 8.8 的 tempered-distribution 极限方法，即可得到 Theorem 8.9 的四象限公式。

### Corollary 8.10

由 Proposition 8.6 / Corollary 8.7 中 `J_+`、`J_-` 的大参数渐近，再对 `rho` 积分作反复分部积分，可得统一于 `epsilon` 的快速衰减：

(94) `|f_epsilon-hat(xi,eta)| <= A_N |xi eta|^{-N}`，当 `|xi eta|>=1/2`，且对每个 `N>=0` 成立。

这说明双曲径向结构带来的自然高频参数不是 `|(xi,eta)|` 本身，而是乘积 `|xi eta|`。

---

## §8.5 求和公式（PDF 411-414）

### 四象限组合核 J

教材把四个象限的振荡积分合并为

`J(lambda)=2[J_+(lambda)+J_+(-lambda)+J_-(lambda)+J_-(-lambda)]`。

### Theorem 8.11：双曲 Poisson 求和公式

若 `f0 in C_c^infinity(0,infinity)`，则

(95)
`sum_{k>=1} f0(k)d(k) = int_0^infinity (log rho+2 gamma)f0(rho)drho + sum_{k>=1} F0(k)d(k)`，

其中

`F0(u)=int_0^infinity J(2 pi u^{1/2}rho) f0(rho^2) rho drho`。

证明对截断函数 `f_epsilon` 使用二维 Poisson 求和。左端按 `mn=k` 分组就是 `sum f0(k)d(k)`。右端分成两类：

1. `mn!=0`：由 Theorem 8.9 和 Corollary 8.10 可逐项令 `epsilon->0`，再按 `|mn|=k` 分组，得到 `sum F0(k)d(k)`；
2. `mn=0`：这是坐标轴与原点的额外贡献，即公式 (96)。

对坐标轴项再使用一维 Poisson 求和，引入

`k_epsilon(y)=sum_{m>=1} eta_epsilon(y/m)/m`。

利用调和和的 Euler 常数渐近得到

(97) `k_epsilon(y)=log(y/epsilon)+gamma+c0+O(epsilon/y)`，

其中 `c0=int_0^1 eta(x)dx/x`。

原点项则引入

`k'_epsilon(y)=int_0^infinity eta(x/epsilon)eta(y/(epsilon x))dx/x`。

按 `x/epsilon` 与 `y/(epsilon x)` 是否大于 1 分区积分，得到

(98) `k'_epsilon(y)=log y - 2 log epsilon + 2c0`。

因此坐标轴总贡献中的截断常数与 `log epsilon` 项恰好抵消，极限只剩

`int_0^infinity (log y+2 gamma)f0(y)dy`，从而证明 Theorem 8.11。

---

## Theorem 8.5 主结果证明：除数问题（PDF 414-417）

目标是

`sum_{k<=mu}d(k)=mu log mu +(2 gamma-1)mu + O(mu^{1/3}log mu)`。

直接把 `f0=chi_(0,mu)` 代入 (95) 不够光滑，因此教材仿照圆盘格点问题，用 `mu=R^2` 并取 `delta=R^{-1/3}`，构造平滑截断 `chi_{mu,delta}`。在 `1<=rho<=R` 它等于 1，在 `R<=rho<=R+delta` 平滑降到 0。

### 积分主项

把它代入 (95) 后，积分项为

(99) `mu log mu +(2 gamma-1)mu + O(mu^{1/3}log mu)`。

### 变换项的两种估计

对 `J` 的主驻相项，需要估计

(100) `sigma^{-1/2} int e^{i sigma rho} chi_{mu,delta}(rho^2) rho^{1/2} drho`。

一次分部积分得到

`O(sigma^{-3/2}R^{1/2}) = O(R^{1/2}k^{-3/4})`；

两次分部积分得到

`O(sigma^{-5/2}R^{1/2}delta^{-1}) = O(R^{1/2}delta^{-1}k^{-5/4})`。

因此在 `k<=delta^{-2}` 用第一种界，在 `k>delta^{-2}` 用第二种界，得到 (101) 的低频/高频分裂。

再用基本加权除数和估计：

- `alpha>-1` 时，`sum_{k<=r}d(k)k^alpha=O(r^{alpha+1}log r)`；
- `alpha<-1` 时，`sum_{k>r}d(k)k^alpha=O(r^{alpha+1}log r)`。

令 `r=delta^{-2}=R^{2/3}`，便把两部分都压到 `O(R^{2/3}log R)`，于是

(102) `N_delta(R)=R^2 log R^2 +(2 gamma-1)R^2 + O(R^{2/3}log R)`。

最后由平滑函数定义得到夹逼

`N_delta(R-delta) <= sum_{k<=mu}d(k) <= N_delta(R+delta)`。

代入 `mu=R^2`、`delta=R^{-1/3}`，即得到 Theorem 8.5 的误差 `O(mu^{1/3}log mu)`。

---

## §9 Exercises（PDF 417-420）

本批已把 Exercise 1-15 分别建立稳定题目锚点：

1. 球坐标下球面测度 Fourier 变换；
2. 含超平面片时 Fourier 衰减不能成立；
3. 一维非退化驻相的完整渐近展开；
4. `k` 阶导数非退化时的 `lambda^{-1/k}` van der Corput 型估计；
5. 曲线 `(t,t^k)` 的有限型最优 Fourier 衰减；
6. 平均算子 `(L^p,L^q)` 三角区域的必要性；
7. `p!=2` 时 `(d-1)/2` 阶平滑的失败；
8. 管状邻域、定义函数与 mollifier 三种方式构造诱导曲面测度；
9. 主曲率在平移、旋转、伸缩下的变换，以及圆锥主曲率；
10. 球面 restriction 公式 (31) 的必要 `p` 范围；
11. 猜想条件 `q<=((d-1)/(d+1))p'` 的必要性；
12. Schrodinger 演化 `e^{it Delta}` 与 Fourier 变换的显式因子分解；
13. Airy 函数 `Ai` 的存在、`(1+|u|)^{-1/4}` 衰减与 `u->+infinity` 的快速衰减；
14. 非齐次 Schrodinger 解算子 `S(F)` 的固定时刻 `L^2` 界与时间连续性；
15. 非线性 Schrodinger 方程 (54) 的质量与能量守恒。

PDF 420 在 Exercise 15 的提示处结束；下一批从 **Exercise 16** 继续。
