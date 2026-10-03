# Live 鏈湴瀛︿範鑱婂ぉ澧為噺

鍩虹嚎鏄數鑴戝凡鏈?`Live_2870261303_Spine38_Windows_x64_preview/resources/app`锛屼笉鏄彟閫犺鑹查」鐩€傚師濮嬪彂甯冩竻鍗曞啓鐨勬槸 `LOCAL_UNVERIFIED`锛涗笉鑳藉啋绉?GitHub 鎻愪氦 `4baf39bf...` 鐨勬瀯寤恒€俙provenance.json` 璁板綍鍘熷 37 涓枃浠剁殑 SHA-256銆傚師绋嬪簭鍜岃鑹叉枃浠跺潎涓嶄慨鏀广€?
## 鍚姩

浣跨敤 Windows PowerShell 鎵ц鏈洰褰?`Start-Live-Study.ps1 -Port 8767`銆傚惎鍔ㄥ櫒鍏堟牳楠屽師婧愮爜鍝堝笇锛屾妸宸叉湁 Electron 杩愯鏃跺拰鏀瑰姩鍚庣殑 app 鏀捐繘宸ヤ綔鍖虹殑鐙珛鍓湰锛屽啀鍚姩鍓湰銆俙-PrepareOnly` 鍙噯澶囷紝涓嶅紑绐楀彛銆?
涓?mygpt 鍏辩敤鐜鍙橀噺 `LIVE_STUDY_TOKEN`锛涗笉瑕佹妸鍑嵁鍐欒繘浠ｇ爜銆佽亰澶╂垨鏃ュ織銆傛湭鎻愪緵鏃跺惎鍔ㄥ櫒浼氬垱寤轰粎褰撳墠 Windows 鐢ㄦ埛鍙鐨勬湰鍦?token 鏂囦欢锛屼綅浜庤繍琛屽壇鏈殑 `study-private/live-token.txt`銆傝鐩綍鍜岀敤鎴烽厤缃潎涓嶅湪婧愮爜浜や粯鐩綍涓€傚彲浼?`-RuntimeSource` 鎸囧畾鍚屼竴鍘熺増鐩綍锛宍-RuntimeDirectory` 蹇呴』鍦ㄥ伐浣滃尯鍐呫€?
榛樿鍙彁渚涙枃瀛楁皵娉″拰鍚屼細璇濆洖澶嶏紱涓嶄細涓诲姩鐢熸垚璇濊锛屼笉鎺ユā鍨嬶紝涓嶅綍闊筹紝涓嶈皟鐢?TTS銆傞€変腑宸叉湁 Spine 瑙掕壊鏃跺鐢ㄥ師鏈夊姩鐢伙紱娌℃湁瑙掕壊鏃舵枃瀛楁樉绀哄湪鐜版湁 Live 鎺у埗鍙帮紝涓嶅亣瑁呭姞杞戒簡 Live2D 妯″瀷銆?
## HTTP 鍚堝悓锛堜粎涓昏繘绋嬶級

鎵€鏈夎姹傞渶 `Authorization: Bearer <LIVE_STUDY_TOKEN>`锛屼粎缁戝畾 `127.0.0.1`锛屾嫆缁濊法 Origin銆侀敊璇?Host銆侀噸澶嶅叧閿ご鍜屽ぇ浜?32 KiB 鐨勮姹傘€傛覆鏌撹繘绋嬩粛绂佹缃戠粶锛孋SP銆乻andbox銆乧ontextIsolation銆乶odeIntegration銆亀ebSecurity 淇濇寔鍘熻缃€?
- `GET /study/health`锛氳繑鍥?`generation` 鍜?`renderer_mode`锛屼笉寰楀綋鎴?dot/model 宸茶繛鎺ャ€?- `POST /study/present`锛氬師 `mygpt.live2d-presentation.v1` 瀛楁锛屽姞 `expires_at`锛堟渶闀垮墿浣?15 绉掞級鍜?`generation`銆傚彧鏈?generation 浠嶇浉绛夈€佸彲淇?renderer 涓?frame 纭 DOM 鏂囧瓧鏄剧ず鍚庯紝鎵嶈繑鍥?`status=presented, display_ack=true, message_id, session_id, renderer_mode`銆傞噸澶?message id 涓嶄細閲嶆樉锛屼篃涓嶈繑鍥炴柊鐨勬垚鍔?ACK銆?- `POST /study/invalidate`锛屾鏂?`{}`锛氬師瀛愰€掑 generation锛屽彇娑堝緟灞曠ず璇锋眰銆佹竻鏂囧瓧鍜屽洖澶嶉槦鍒楋紝杩斿洖鏂?generation銆傛棫 HTTP 璇锋眰鍗充娇鏅氬埌锛屼篃涓嶈兘璺ㄦ浠ｉ檯鏄剧ず銆?- `POST /study/replies/take`锛屾鏂?`{ "session_id": "..." }`锛氬彧鍙栬浼氳瘽鐨勪竴鏉?`mygpt.live-user-reply.v1`锛坮equest_id銆乻ession_id銆乺eply_to_message_id銆乼ext銆乧aptured_at锛夈€傚洖澶嶄笉寰楃洿鎺ユ墽琛屾ā鍨嬶紝浠嶉』 mygpt 楠岃瘉褰撳墠 Book 鐘舵€佸強浼氳瘽銆?
mygpt 蹇呴』鍦?presentation 鐢熷懡鍛ㄦ湡寮€濮嬫崟鑾锋湰鍦板け鏁堝簭鍙凤紱璇诲彇 health 鍚庡鏋滆搴忓彿鍙樺寲鍒欐斁寮冦€傞殢鍚庡彂閫佹崟鑾风殑鏈嶅姟绔?generation锛屼笉鑳界粰鏃ф秷鎭埛鏂?generation銆侶TTP 瓒呮椂缁撴灉鏈煡锛屼笉鑷姩閲嶈瘯銆侫CK 鍚庝粛闇€鍐嶆鏌?Book 绉熺害銆傞殣钘忔祴璇?renderer 鐨?`renderer_mode=offscreen_test` 蹇呴』鐢辩敓浜ч€傞厤鍣ㄦ嫆缁濓紱娴嬭瘯鍙湁鏄惧紡鎺堟潈鎵嶆帴鍙椼€?
## 宸茶瀵熶笌鏈畬鎴?
鐪熷疄 Electron 44.4.4 闅愯棌绐楀彛宸查獙璇侊細DOM 鏂囧瓧鑰岄潪 HTML 鎵ц銆佸彲淇?sender 涓ゅ抚 ACK銆佺湡瀹炶〃鍗曡緭鍏ュ悓浼氳瘽鍙栧洖涓€娆°€佽繃鏈?鍋滅敤鎾ら攢銆佷吉 ACK 鎷掔粷銆佹棫璇锋眰璺ㄦ挙閿€浠ｉ檯鎷掔粷銆傛祴璇曠敾闈㈡槑纭爣娉ㄢ€滄湰鍦伴殣钘忕獥鍙ｆ祴璇曗€濓紱杩欎笉鏄敤鎴峰凡鐪嬪埌瑙掕壊銆佽闊虫垨妯″瀷鐢熸垚鍐呭鐨勮瘉鏄庛€?
鍘熻鑹茶祫婧愬姞杞戒笌妯″瀷璋冪敤涓嶅湪鏈鑷姩娴嬭瘯涓紱妯″瀷鎸夌敤鎴疯姹傛殏涓嶆帴鍏ャ€備笉寮€鍏綉绔彛锛屼笉鏀瑰彉鍘熷簲鐢ㄦ潈闄愶紝涓嶈嚜鍔ㄥ鍏ョ鏈夎鑹茶祫婧愩€?
