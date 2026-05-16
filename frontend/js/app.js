let ws=null,myName="",currentChat=null;
let allUsers=[],onlineUsers=[],unreadCounts={};
let lastSender="",lastTs="";
let typingTimers={},myTypingTimer=null;
let emojiOpen=false,searchOpen=false,notifOpen=false,optionsOpen=false;
let currentPreviewSrc="";
let isDark=true;
let notifications=[],unreadNotifCount=0;
let roomMuted=false,pinnedMessages=[];
let usernameCheckTimer=null;
let amAdmin=false,usersData=[],privateRooms=[];
let adminTab="all";
let replyTo=null,replyText=null,replySender=null;
let polls={};
let privateRoomAction="join",privateRoomTarget="";

const COLORS=["#5865f2","#23a55a","#f0b232","#eb459e","#ed4245","#57f287"];
function userColor(n){let h=0;for(let c of n)h=c.charCodeAt(0)+((h<<5)-h);return COLORS[Math.abs(h)%COLORS.length];}
const ROOM_DESC={general:"General discussion",random:"Random talks",tech:"Tech and development"};
const QUICK_REACTIONS=["👍","❤️","😂","😮","😢","🔥","👏","🎉"];

const EMOJIS={
  "Love & Hearts":["❤️","🧡","💛","💚","💙","💜","🖤","🤍","🤎","💔","❣️","💕","💞","💓","💗","💖","💘","💝","💟","😍","🥰","😘","😗","😙","😚","💑","👫","👬","👭","💏","🫶","🤗","😻","💋","💌","🌹","🌷","💐"],
  "Smileys":["😀","😃","😄","😁","😆","😅","😂","🤣","😊","😇","🙂","🙃","😉","😌","😎","🤩","🥳","😏","😒","😞","😔","😟","😕","🙁","😣","😖","😫","😩","🥺","😢","😭","😤","😠","😡","🤬","🤯","😳","🥵","🥶","😱","😨","😰","😥","😓","🤔","🤭","🤫","🤥","😶","😐","😑","😬","🙄","😯","😦","😧","😮","😲","🥱","😴","🤤","😪","😵","🤐","🥴","🤢","🤮","🤧","😷","🤒","🤕"],
  "Cute & Fun":["🥺","🥹","😺","😸","😹","😻","😼","😽","🙀","😿","😾","🐱","🐶","🐰","🐻","🐼","🐨","🐯","🦊","🐸","🐵","🙈","🙉","🙊","🐧","🐦","🦋","🌸","🌺","🌻","🌼","🌷","🌹","💮","🏵","🎀","🎁","🎊","🎉","✨","💫","⭐","🌟","🌈","☀️","🌙","⚡","❄️"],
  "Gestures":["👋","🤚","🖐","✋","🖖","👌","🤌","🤏","✌️","🤞","🤟","🤘","🤙","👈","👉","👆","👇","☝️","👍","👎","✊","👊","🤛","🤜","👏","🙌","👐","🤲","🤝","🙏","💪","🦾","✍️","🤳"],
  "Animals":["🐶","🐱","🐭","🐹","🐰","🦊","🐻","🐼","🐨","🐯","🦁","🐮","🐷","🐸","🐵","🙈","🙉","🙊","🐔","🐧","🐦","🦆","🦅","🦉","🦇","🐺","🐴","🦄","🐝","🦋","🐌","🐞","🐢","🐍","🦎","🐙","🦑","🐬","🐳","🐋","🦈","🐊","🐘","🦒","🦙","🐕","🐈","🦚","🦜","🦢","🦩","🕊","🐇","🦝","🦨","🦡","🦫","🦦","🦥","🐁","🐀","🐿","🦔"],
  "Food":["🍎","🍊","🍋","🍇","🍓","🫐","🍒","🍑","🥭","🍍","🥥","🥝","🍅","🍆","🥑","🥦","🥕","🌽","🍔","🍟","🍕","🌮","🌯","🍜","🍣","🍱","🍛","🍰","🎂","🍩","🍪","🍫","🍬","🍭","☕","🍵","🧃","🥤","🧋","🍺","🍻","🥂","🍷","🍸","🍹","🧁","🍮","🍡","🍧","🍨","🍦"],
  "Activities":["⚽","🏀","🏈","⚾","🎾","🏐","🎱","🏓","🏸","⛳","🎣","🥊","🎽","🛹","⛷","🏂","🏋️","🤸","🏊","🚴","🧘","🏄","🎮","🕹","🎲","🎯","🎳","🎪","🎭","🎨","🎬","🎤","🎧","🎼","🎵","🎶","🎹","🥁","🎷","🎺","🎸","🪕","🎻"],
  "Travel":["🚗","🚕","🚙","🚌","🏎","🚓","🚑","🚒","🛻","🚚","🏍","🛵","🚲","🛴","✈️","🚀","🛸","🚁","⛵","🚤","🚢","🗺","🧭","🏔","⛰","🌋","🏕","🏖","🏜","🏝","🏠","🏡","🏢","🏥","🏦","🏨","🏪","🏫","🏬","🗼","🗽","⛪","🕌","⛩","🌁","🌃","🌄","🌅","🌆","🌇","🌉","🌌","🎠","🎡","🎢","🎪"],
  "Symbols":["💯","🔥","✨","⭐","🌟","💫","❄️","🌈","☀️","⛅","🌧","⛈","🌊","💧","💦","🎉","🎊","🎈","🎁","🏆","🥇","🥈","🥉","🎖","🏅","🔔","🔕","🎵","🎶","💡","🔍","🔑","🔒","🔓","💻","📱","📷","🎮","🕹","🎲","♠️","♥️","♦️","♣️","🔮","🪄","🧿","☯️","☮️","✝️","☪️","🕉","♻️","✅","❎","❌","⭕","🛑","⛔","🚫","💢","🆗","🆙","🆒","🆕","🆓"],
};
const EMOJI_ICONS={"Love & Hearts":"❤️","Smileys":"😀","Cute & Fun":"🥺","Gestures":"👋","Animals":"🐶","Food":"🍎","Activities":"⚽","Travel":"🚗","Symbols":"💯"};

function saveSession(u,p){sessionStorage.setItem("fc_u",u);sessionStorage.setItem("fc_p",p);}
function clearSession(){sessionStorage.removeItem("fc_u");sessionStorage.removeItem("fc_p");}
function getSaved(){return{u:sessionStorage.getItem("fc_u"),p:sessionStorage.getItem("fc_p")};}
function toggleTheme(){isDark=!isDark;document.body.classList.toggle("light",!isDark);sessionStorage.setItem("fc_theme",isDark?"dark":"light");}
function openSidebar(){document.getElementById("sidebar").classList.add("open");document.getElementById("sidebar-overlay").classList.add("show");}
function closeSidebar(){document.getElementById("sidebar").classList.remove("open");document.getElementById("sidebar-overlay").classList.remove("show");}
function showReg(){document.getElementById("login-card").style.display="none";document.getElementById("reg-card").style.display="flex";document.getElementById("reg-error").textContent="";}
function showLogin(){document.getElementById("reg-card").style.display="none";document.getElementById("login-card").style.display="flex";document.getElementById("auth-error").textContent="";}
function togglePwd(id){const i=document.getElementById(id);i.type=i.type==="password"?"text":"password";}

const validators={
  fullname:{validate(v){if(!v)return{ok:false,msg:"Full name is required",type:"error"};if(v.length<2)return{ok:false,msg:"At least 2 characters required",type:"error"};if(!/^[a-zA-Z\s'-]+$/.test(v))return{ok:false,msg:"Letters only",type:"error"};return{ok:true,msg:"✓ Looks good!",type:"success"};}},
  username:{validate(v){if(!v)return{ok:false,msg:"Username is required",type:"error"};if(v.length<3)return{ok:false,msg:"At least 3 characters required",type:"error"};if(!/^[a-zA-Z0-9_]+$/.test(v))return{ok:false,msg:"Letters, numbers and underscore only",type:"error"};if(v.length>24)return{ok:false,msg:"Max 24 characters",type:"error"};return{ok:true,msg:"✓ Checking availability...",type:"info"};}},
  password:{validate(v){if(!v)return{ok:false,msg:"Password is required",type:"error"};if(v.length<6)return{ok:false,msg:"At least 6 characters required",type:"error"};if(v.length<8)return{ok:false,msg:"Use 8+ characters for better security",type:"info"};if(!/(?=.*[A-Z])/.test(v))return{ok:false,msg:"Add at least one uppercase letter",type:"error"};if(!/(?=.*[0-9])/.test(v))return{ok:false,msg:"Add at least one number",type:"error"};return{ok:true,msg:"✓ Strong password!",type:"success"};}},
  confirm:{validate(v){const pwd=document.getElementById("reg-password").value;if(!v)return{ok:false,msg:"Please confirm your password",type:"error"};if(v!==pwd)return{ok:false,msg:"❌ Passwords do not match",type:"error"};return{ok:true,msg:"✓ Passwords match!",type:"success"};}},
  terms:{validate(){return document.getElementById("terms-chk").checked?{ok:true,msg:"",type:"success"}:{ok:false,msg:"You must agree to continue",type:"error"};}}
};

const fieldValid={fullname:false,username:false,password:false,confirm:false,terms:false};
const inputIds={fullname:"reg-fullname",username:"reg-username",password:"reg-password",confirm:"reg-confirm"};

function validateField(field){
  const val=inputIds[field]?document.getElementById(inputIds[field])?.value?.trim()||"":" ";
  const result=validators[field].validate(val===" "?"":val);
  const msgEl=document.getElementById(`msg-${field}`);
  if(msgEl){msgEl.textContent=result.msg;msgEl.className=`field-msg ${result.type}`;}
  const input=inputIds[field]?document.getElementById(inputIds[field]):null;
  if(input){const hasVal=input.value.length>0;input.className=hasVal?(result.ok&&field!=="username"?"valid":"invalid"):"";const statusEl=document.getElementById(`status-${field}`);if(statusEl)statusEl.textContent=hasVal?(result.ok&&field!=="username"?"✅":"❌"):"";}
  if(field==="password")checkStr(document.getElementById("reg-password").value);
  if(field==="password"&&document.getElementById("reg-confirm").value)validateField("confirm");
  if(field==="username"&&result.ok){fieldValid.username=false;if(usernameCheckTimer)clearTimeout(usernameCheckTimer);usernameCheckTimer=setTimeout(()=>checkUsernameAvailability(document.getElementById("reg-username").value.trim()),600);}
  else{if(field!=="username")fieldValid[field]=result.ok;}
  if(field!=="username")updateRegBtn();
}

async function checkUsernameAvailability(username){
  const statusEl=document.getElementById("status-username");const msgEl=document.getElementById("msg-username");const input=document.getElementById("reg-username");
  statusEl.textContent="⏳";msgEl.textContent="Checking availability...";msgEl.className="field-msg info";
  try{const res=await fetch(`/check-username/${encodeURIComponent(username)}`);const data=await res.json();
    if(data.available){statusEl.textContent="✅";msgEl.textContent="✓ Username is available!";msgEl.className="field-msg success";input.className="valid";fieldValid.username=true;}
    else{statusEl.textContent="❌";msgEl.textContent="❌ Username already taken";msgEl.className="field-msg error";input.className="invalid";fieldValid.username=false;}
  }catch(e){statusEl.textContent="";msgEl.textContent="Could not check";msgEl.className="field-msg info";fieldValid.username=false;}
  updateRegBtn();
}

function updateRegBtn(){const allValid=Object.values(fieldValid).every(Boolean);document.getElementById("reg-btn").disabled=!allValid;}

function checkStr(val){
  const bars=["b1","b2","b3","b4"].map(id=>document.getElementById(id));const lbl=document.getElementById("s-label");
  bars.forEach(b=>b.className="s-bar");if(!val){lbl.textContent="";return;}
  let s=0;if(val.length>=6)s++;if(val.length>=10)s++;if(/[A-Z]/.test(val)&&/[0-9]/.test(val))s++;if(/[^A-Za-z0-9]/.test(val))s++;
  const lvls=["weak","fair","good","strong"],lbls=["Weak","Fair","Good","Strong"];
  for(let i=0;i<s;i++)bars[i].className=`s-bar ${lvls[s-1]}`;lbl.textContent=lbls[s-1]||"";lbl.className=`s-label ${lvls[s-1]||""}`;
}

function doAuth(action){const u=document.getElementById("auth-username").value.trim();const p=document.getElementById("auth-password").value.trim();if(!u||!p){document.getElementById("auth-error").textContent="Please enter username and password.";return;}connectWS(action,u,p);}

function doRegister(){
  fieldValid.fullname=validators.fullname.validate(document.getElementById("reg-fullname").value.trim()).ok;
  fieldValid.password=validators.password.validate(document.getElementById("reg-password").value.trim()).ok;
  fieldValid.confirm=validators.confirm.validate(document.getElementById("reg-confirm").value.trim()).ok;
  fieldValid.terms=document.getElementById("terms-chk").checked;
  const u=document.getElementById("reg-username").value.trim();const p=document.getElementById("reg-password").value.trim();
  if(!u||!p||!Object.values(fieldValid).every(Boolean)){document.getElementById("reg-error").textContent="Please fix all errors.";return;}
  document.getElementById("reg-error").textContent="";
  connectWS("register",u,p);
}

function logout(){clearSession();location.reload();}

function connectWS(action,username,password){
  const proto=location.protocol==="https:"?"wss":"ws";
  ws=new WebSocket(`${proto}://${location.host}/ws`);
  ws.onopen=()=>ws.send(JSON.stringify({action,username,password}));
  ws.onmessage=e=>{
    const m=JSON.parse(e.data);
    if(m.type==="pong")return;
    if(action==="register"&&m.type==="auth_ok"){
      ws.close();
      document.getElementById("reg-error").style.color="var(--green)";
      document.getElementById("reg-error").textContent="✅ Account created! Redirecting to login...";
      setTimeout(()=>{
        document.getElementById("reg-error").textContent="";
        document.getElementById("reg-error").style.color="";
        showLogin();
        document.getElementById("auth-username").value=username;
      },2000);
      return;
    }
    handleMsg(m);
  };
  ws.onclose=()=>{setTimeout(()=>{const {u,p}=getSaved();if(u&&p)connectWS("login",u,p);},3000);};
  if(action==="login")saveSession(username,password);
}

function handleMsg(msg){
  if(msg.type==="auth_fail"){clearSession();const r=document.getElementById("reg-card").style.display!=="none";if(r)document.getElementById("reg-error").textContent=msg.text;else document.getElementById("auth-error").textContent=msg.text;ws.close();return;}
  if(msg.type==="force_logout"){clearSession();alert(msg.text);location.reload();return;}
  if(msg.type==="promoted"){alert(msg.text);amAdmin=true;document.getElementById("admin-panel-btn").style.display="flex";document.getElementById("up-tag").textContent="👑 Admin";return;}
  if(msg.type==="auth_ok"){
    myName=msg.username;allUsers=msg.all_users;onlineUsers=msg.online_users;
    amAdmin=msg.is_admin||false;usersData=msg.users_data||[];privateRooms=msg.private_rooms||[];
    document.getElementById("auth-overlay").style.display="none";
    document.getElementById("app").style.display="flex";
    document.getElementById("my-uname").textContent=myName;
    document.getElementById("up-name").textContent=myName;
    const av=document.getElementById("up-av");av.style.background=userColor(myName);av.innerHTML=myName[0].toUpperCase()+'<div class="up-st"></div>';
    document.getElementById("msg-input").disabled=false;document.getElementById("send-btn").disabled=false;
    if(amAdmin){document.getElementById("admin-panel-btn").style.display="flex";document.getElementById("up-tag").textContent="👑 Admin";}
    buildRooms(msg.rooms);buildPrivateRooms();buildContacts();updateCount();buildEmojiPicker();requestNotifPerm();return;
  }
  if(msg.type==="user_online"){onlineUsers=msg.online_users;if(msg.all_users)allUsers=msg.all_users;buildContacts();updateCount();return;}
  if(msg.type==="user_offline"){onlineUsers=msg.online_users;if(msg.all_users)allUsers=msg.all_users;buildContacts();updateCount();return;}
  if(msg.type==="system_admin"){if(msg.users_data)usersData=msg.users_data;addSys(msg.text);return;}
  if(msg.type==="admin_users_list"){usersData=msg.users_data;onlineUsers=msg.online_users;renderAdminContent();return;}
  if(msg.type==="private_room_created"){privateRooms=msg.private_rooms||[];buildPrivateRooms();addSys(`🔒 New private room: #${msg.room.name}`);return;}
  if(msg.type==="join_private_ok"){document.getElementById("private-room-modal").classList.remove("show");document.getElementById("ch-icon").textContent="🔒";document.getElementById("ch-title").textContent=msg.room;document.getElementById("ch-topic").textContent="Private Room";document.getElementById("msg-input").placeholder=`Message #${msg.room}`;setActive(`private-${msg.room}`);currentChat={type:"room",id:msg.room};return;}
  if(msg.type==="join_private_fail"){document.getElementById("private-room-error").textContent=msg.text;return;}
  if(msg.type==="polls_list"){if(msg.polls)msg.polls.forEach(p=>{polls[p.id]=p;});renderPolls();return;}
  if(msg.type==="new_poll"){polls[msg.poll.id]=msg.poll;renderPolls();addSys(`📊 ${msg.poll.creator} created a poll: "${msg.poll.question}"`);return;}
  if(msg.type==="poll_update"){if(polls[msg.poll_id])polls[msg.poll_id].votes=msg.votes;renderPolls();return;}
  if(msg.type==="reaction_update"){const el=document.getElementById(`msg-${msg.id}`);if(el){const reactDiv=el.querySelector(".msg-reactions");if(reactDiv)reactDiv.innerHTML=renderReactionBadges(msg.id,msg.reactions,msg.msg_type);}return;}
  if(msg.type==="history"){if(currentChat?.type==="room"&&currentChat?.id===msg.room){clearMsgs();addDateDiv("Today");msg.messages.forEach(m=>addMsg(m.id,m.sender,m.text,m.timestamp,m.sender===myName,m.edited,m.reply_to,m.reply_text,m.reply_sender,m.reactions||{}));renderPolls();}return;}
  if(msg.type==="dm_history"){if(currentChat?.type==="dm"&&currentChat?.id===msg.with){clearMsgs();addDateDiv("Today");msg.messages.forEach(m=>addMsg(m.id,m.sender,m.text,m.timestamp,m.sender===myName,m.edited,m.reply_to,m.reply_text,m.reply_sender,m.reactions||{}));}return;}
  if(msg.type==="system"){if(currentChat?.type==="room")addSys(msg.text);updateCount();return;}
  if(msg.type==="message"){if(currentChat?.type==="room"&&currentChat?.id===msg.room)addMsg(msg.id,msg.sender,msg.text,msg.timestamp,msg.sender===myName,msg.edited,msg.reply_to,msg.reply_text,msg.reply_sender,msg.reactions||{});else if(msg.sender!==myName&&!roomMuted)showNotif(msg.sender,msg.text,"room");return;}
  if(msg.type==="dm"){const other=msg.sender===myName?msg.receiver:msg.sender;if(currentChat?.type==="dm"&&currentChat?.id===other)addMsg(msg.id,msg.sender,msg.text,msg.timestamp,msg.sender===myName,msg.edited,msg.reply_to,msg.reply_text,msg.reply_sender,msg.reactions||{});else if(msg.sender!==myName){unreadCounts[msg.sender]=(unreadCounts[msg.sender]||0)+1;buildContacts();showNotif(msg.sender,msg.text,"dm");}return;}
  if(msg.type==="typing"){const name=msg.username;if(name===myName)return;if(msg.is_dm&&currentChat?.type==="dm"&&currentChat?.id===name)showTyping(name);else if(!msg.is_dm&&currentChat?.type==="room"&&currentChat?.id===msg.room)showTyping(name);return;}
  if(msg.type==="search_results"){showSearchResults(msg.results,msg.query);return;}
  if(msg.type==="message_edited"){const el=document.getElementById(`msg-${msg.id}`);if(el){const textEl=el.querySelector(".msg-text");if(textEl)textEl.textContent=msg.text;const head=el.querySelector(".msg-head");if(head&&!head.querySelector(".msg-edited")){const e=document.createElement("span");e.className="msg-edited";e.textContent=" (edited)";head.appendChild(e);}}return;}
  if(["call_offer","call_answer","call_ice","call_reject","call_end"].includes(msg.type)){handleCallMsg(msg);return;}
  if(msg.type==="message_deleted"){const el=document.getElementById(`msg-${msg.id}`);if(el){const textEl=el.querySelector(".msg-text,.msg-img");if(textEl){textEl.className="msg-deleted";textEl.textContent="This message was deleted.";}const actions=el.querySelector(".msg-actions");if(actions)actions.remove();}return;}
}

// ── REPLY ──────────────────────────────
function setReply(id,sender,text){
  replyTo=id;replySender=sender;replyText=text;
  document.getElementById("reply-bar").classList.add("show");
  document.getElementById("reply-bar-sender").textContent=sender;
  document.getElementById("reply-bar-text").textContent=text.startsWith("[IMAGE]")?"📷 Image":text;
  document.getElementById("msg-input").focus();
}
function cancelReply(){replyTo=null;replySender=null;replyText=null;document.getElementById("reply-bar").classList.remove("show");}

// ── REACTIONS ──────────────────────────────
function renderReactionBadges(msgId,reactions,msgType){
  if(!reactions||Object.keys(reactions).length===0)return"";
  return Object.entries(reactions).map(([emoji,users])=>{
    const isMine=users.includes(myName);
    return `<span class="reaction-badge${isMine?" mine":""}" onclick="sendReaction(${msgId},'${emoji}','${msgType||"room"}')" title="${users.join(", ")}">${emoji}<span class="reaction-count">${users.length}</span></span>`;
  }).join("");
}

function sendReaction(msgId,emoji,msgType){
  if(!ws||ws.readyState!==WebSocket.OPEN)return;
  const other=currentChat?.type==="dm"?currentChat.id:null;
  ws.send(JSON.stringify({type:"react",id:msgId,emoji,msg_type:msgType||"room",other}));
}

function showReactionPicker(msgId,msgType,btnEl){
  document.querySelectorAll(".reaction-picker").forEach(p=>p.remove());
  const picker=document.createElement("div");
  picker.className="reaction-picker";
  const rect=btnEl.getBoundingClientRect();
  picker.style.position="fixed";
  picker.style.bottom=(window.innerHeight-rect.top+4)+"px";
  picker.style.right=(window.innerWidth-rect.right)+"px";
  QUICK_REACTIONS.forEach(emoji=>{
    const btn=document.createElement("button");
    btn.className="reaction-emoji";btn.textContent=emoji;
    btn.onclick=()=>{sendReaction(msgId,emoji,msgType);picker.remove();};
    picker.appendChild(btn);
  });
  document.body.appendChild(picker);
  setTimeout(()=>document.addEventListener("click",function remove(e){if(!picker.contains(e.target)){picker.remove();document.removeEventListener("click",remove);}},true),10);
}

// ── POLLS ──────────────────────────────
function openCreatePollModal(){closeOptionsMenu();document.getElementById("poll-modal").classList.add("show");document.getElementById("poll-question").value="";document.getElementById("poll-error").textContent="";document.getElementById("poll-options-wrap").innerHTML='<div class="poll-option-input"><input type="text" placeholder="Option 1" maxlength="100"/></div><div class="poll-option-input"><input type="text" placeholder="Option 2" maxlength="100"/></div>';}
function closePollModal(){document.getElementById("poll-modal").classList.remove("show");}
function addPollOption(){const wrap=document.getElementById("poll-options-wrap");const count=wrap.children.length+1;if(count>6)return;const div=document.createElement("div");div.className="poll-option-input";div.innerHTML=`<input type="text" placeholder="Option ${count}" maxlength="100"/>`;wrap.appendChild(div);}
function submitPoll(){
  const question=document.getElementById("poll-question").value.trim();
  const inputs=document.querySelectorAll("#poll-options-wrap input");
  const options=[...inputs].map(i=>i.value.trim()).filter(Boolean);
  if(!question){document.getElementById("poll-error").textContent="Please enter a question!";return;}
  if(options.length<2){document.getElementById("poll-error").textContent="Need at least 2 options!";return;}
  ws.send(JSON.stringify({type:"create_poll",question,options}));
  closePollModal();
}

function renderPolls(){
  const box=document.getElementById("messages");
  document.querySelectorAll(".poll-card").forEach(p=>p.remove());
  Object.values(polls).forEach(poll=>{
    if(currentChat?.type==="room"&&poll.room===currentChat.id){
      const card=document.createElement("div");
      card.className="poll-card";card.id=`poll-${poll.id}`;
      const totalVotes=Object.values(poll.votes).reduce((a,b)=>a+b.length,0);
      const myVote=Object.entries(poll.votes).find(([,users])=>users.includes(myName))?.[0];
      card.innerHTML=`<div class="poll-creator">📊 Poll by ${esc(poll.creator)}</div><div class="poll-question">${esc(poll.question)}</div>${poll.options.map(opt=>{const votes=poll.votes[opt]||[];const pct=totalVotes>0?Math.round(votes.length/totalVotes*100):0;const isVoted=myVote===opt;return `<div class="poll-option" onclick="voteOnPoll(${poll.id},'${esc(opt)}')"><div class="poll-option-bar"><div class="poll-option-fill${isVoted?" voted":""}" style="width:${pct}%"></div><span class="poll-option-label">${isVoted?"✓ ":""}${esc(opt)}</span><span class="poll-option-pct">${pct}%</span></div></div>`;}).join("")}<div class="poll-meta">${totalVotes} vote${totalVotes!==1?"s":""} • ${formatTs(poll.timestamp)}</div>`;
      box.appendChild(card);
    }
  });
  box.scrollTop=box.scrollHeight;
}

function voteOnPoll(pollId,option){
  if(!ws||ws.readyState!==WebSocket.OPEN)return;
  ws.send(JSON.stringify({type:"vote_poll",poll_id:pollId,option}));
}

// ── PRIVATE ROOMS ──────────────────────────────
function buildPrivateRooms(){
  const list=document.getElementById("private-room-list");
  if(privateRooms.length===0){list.innerHTML=`<div style="padding:6px 16px;font-size:.75rem;color:var(--text-dim)">No private rooms</div>`;return;}
  list.innerHTML=privateRooms.map(r=>`<div class="ch-item" id="private-${r.name}" onclick="joinPrivateRoom('${r.name}')"><span class="ch-lock-icon">🔒</span><div class="ch-info"><div class="ch-name">${esc(r.name)}</div><div class="ch-desc-small">by ${esc(r.creator)}</div></div></div>`).join("");
}

function joinPrivateRoom(name){
  privateRoomAction="join";privateRoomTarget=name;
  document.getElementById("private-room-modal-title").textContent=`🔒 Join #${name}`;
  document.getElementById("private-room-name-wrap").style.display="none";
  document.getElementById("private-room-submit").textContent="Join";
  document.getElementById("private-room-password").value="";
  document.getElementById("private-room-error").textContent="";
  document.getElementById("private-room-modal").classList.add("show");
  setTimeout(()=>document.getElementById("private-room-password").focus(),100);
}

function openCreatePrivateRoom(){
  privateRoomAction="create";
  document.getElementById("private-room-modal-title").textContent="🔒 Create Private Room";
  document.getElementById("private-room-name-wrap").style.display="block";
  document.getElementById("private-room-submit").textContent="Create";
  document.getElementById("private-room-name").value="";
  document.getElementById("private-room-password").value="";
  document.getElementById("private-room-error").textContent="";
  document.getElementById("private-room-modal").classList.add("show");
  setTimeout(()=>document.getElementById("private-room-name").focus(),100);
}

function closePrivateRoomModal(){document.getElementById("private-room-modal").classList.remove("show");}

function submitPrivateRoom(){
  const password=document.getElementById("private-room-password").value.trim();
  if(!password){document.getElementById("private-room-error").textContent="Password required!";return;}
  if(privateRoomAction==="create"){
    const name=document.getElementById("private-room-name").value.trim().replace(/\s+/g,"_");
    if(!name){document.getElementById("private-room-error").textContent="Room name required!";return;}
    ws.send(JSON.stringify({type:"create_private_room",room:name,password}));
    closePrivateRoomModal();
  } else {
    ws.send(JSON.stringify({type:"join_private_room",room:privateRoomTarget,password}));
  }
}

// ── ADMIN ──────────────────────────────
function openAdminPanel(){document.getElementById("admin-panel").classList.add("show");ws.send(JSON.stringify({type:"admin_get_users"}));}
function closeAdminPanel(){document.getElementById("admin-panel").classList.remove("show");}
function switchAdminTab(tab){adminTab=tab;document.querySelectorAll(".admin-tab").forEach(t=>t.classList.remove("active"));document.getElementById(`tab-${tab}`).classList.add("active");renderAdminContent();}
function renderAdminContent(){
  const content=document.getElementById("admin-content");
  let users=usersData;
  if(adminTab==="online")users=usersData.filter(u=>onlineUsers.includes(u.username));
  else if(adminTab==="banned")users=usersData.filter(u=>u.is_banned);
  const total=usersData.length,online=usersData.filter(u=>onlineUsers.includes(u.username)).length,banned=usersData.filter(u=>u.is_banned).length;
  content.innerHTML=`<div class="admin-stats"><div class="admin-stat"><div class="admin-stat-num">${total}</div><div class="admin-stat-label">Total Users</div></div><div class="admin-stat"><div class="admin-stat-num" style="color:var(--green)">${online}</div><div class="admin-stat-label">Online</div></div><div class="admin-stat"><div class="admin-stat-num" style="color:var(--red)">${banned}</div><div class="admin-stat-label">Banned</div></div></div>${users.map(u=>{const isOnline=onlineUsers.includes(u.username);const isMe=u.username===myName;return`<div class="admin-user-item"><div class="admin-user-av" style="background:${userColor(u.username)}">${u.username[0].toUpperCase()}</div><div class="admin-user-info"><div class="admin-user-name">${esc(u.username)}${u.is_admin?'<span class="admin-badge admin">👑 Admin</span>':''}${u.is_banned?'<span class="admin-badge banned">🚫 Banned</span>':''}<span class="admin-badge ${isOnline?'online':'offline'}">${isOnline?'● Online':'○ Offline'}</span></div></div>${!isMe?`<div class="admin-user-btns">${isOnline&&!u.is_banned?`<button class="admin-action-btn kick" onclick="adminKick('${u.username}');closeAdminPanel()">Kick</button>`:''}${!u.is_banned?`<button class="admin-action-btn ban" onclick="adminBan('${u.username}');closeAdminPanel()">Ban</button>`:''}${u.is_banned?`<button class="admin-action-btn unban" onclick="adminUnban('${u.username}')">Unban</button>`:''}${!u.is_admin?`<button class="admin-action-btn promote" onclick="adminMakeAdmin('${u.username}');closeAdminPanel()">Admin</button>`:''}${u.is_admin?`<button class="admin-action-btn demote" onclick="adminRemoveAdmin('${u.username}');closeAdminPanel()">Remove</button>`:''}<button class="admin-action-btn ban" onclick="adminDelete('${u.username}')" style="background:#8b0000;">🗑️</button></div>`:''}`;}).join('')}`;
}
function adminKick(username){if(!confirm(`Kick ${username}?`))return;ws.send(JSON.stringify({type:"admin_kick",username}));}
function adminDelete(username){if(!confirm(`PERMANENTLY DELETE ${username}? This cannot be undone!`))return;ws.send(JSON.stringify({type:"admin_delete_user",username}));closeAdminPanel();}
function adminBan(username){if(!confirm(`Ban ${username}?`))return;ws.send(JSON.stringify({type:"admin_ban",username}));closeProfile();}
function adminUnban(username){if(!confirm(`Unban ${username}?`))return;ws.send(JSON.stringify({type:"admin_unban",username}));}
function adminMakeAdmin(username){if(!confirm(`Make ${username} an admin?`))return;ws.send(JSON.stringify({type:"admin_make_admin",username}));closeProfile();}
function adminRemoveAdmin(username){if(!confirm(`Remove admin from ${username}?`))return;ws.send(JSON.stringify({type:"admin_remove_admin",username}));closeProfile();}

function requestNotifPerm(){if("Notification" in window&&Notification.permission==="default")Notification.requestPermission();}
function showNotif(sender,text,type){
  addNotification(type,type==="dm"?`<strong>${esc(sender)}</strong> sent you a DM: "${esc(text.startsWith("[IMAGE]")?"📷 Image":text)}"`:
    `<strong>${esc(sender)}</strong> in <strong>#${currentChat?.id||"general"}</strong>: "${esc(text.startsWith("[IMAGE]")?"📷 Image":text)}"`,sender);
  const toast=document.createElement("div");toast.className="notif-toast";
  toast.innerHTML=`<div class="notif-av" style="background:${userColor(sender)}">${sender[0].toUpperCase()}</div><div class="notif-body"><div class="notif-name">${esc(sender)}</div><div class="notif-text">${esc(text.startsWith("[IMAGE]")?"📷 Image":text)}</div></div>`;
  toast.onclick=()=>{if(type==="dm")openDM(sender);document.body.removeChild(toast);};
  document.body.appendChild(toast);setTimeout(()=>{if(document.body.contains(toast))document.body.removeChild(toast);},4000);
  if("Notification" in window&&Notification.permission==="granted"&&document.hidden)new Notification(sender,{body:text.startsWith("[IMAGE]")?"📷 Sent an image":text});
}
function addNotification(type,text,sender){const notif={id:Date.now(),type,text,sender,time:new Date().toLocaleTimeString([],{hour:"2-digit",minute:"2-digit"}),unread:true};notifications.unshift(notif);if(notifications.length>20)notifications.pop();if(!notifOpen){unreadNotifCount++;document.getElementById("notif-count").style.display="block";}if(notifOpen)renderNotifs();}
function toggleNotifPanel(){notifOpen=!notifOpen;closeOtherPanels("notif");document.getElementById("notif-panel").classList.toggle("show",notifOpen);document.getElementById("notif-toggle").classList.toggle("active",notifOpen);if(notifOpen){unreadNotifCount=0;document.getElementById("notif-count").style.display="none";renderNotifs();}}
function renderNotifs(){const list=document.getElementById("notif-list");if(notifications.length===0){list.innerHTML='<div class="notif-empty">&#128276; No notifications yet</div>';return;}list.innerHTML=notifications.map(n=>`<div class="notif-item ${n.unread?'unread':''}" onclick="handleNotifClick('${n.type}','${n.sender||''}')"><div class="notif-item-icon" style="background:${userColor(n.sender||'system')}">${n.type==='dm'?'&#128172;':n.type==='room'?'#':'&#128276;'}</div><div class="notif-item-body"><div class="notif-item-text">${n.text}</div><div class="notif-item-time">${n.time}</div></div></div>`).join("");notifications.forEach(n=>n.unread=false);}
function handleNotifClick(type,sender){if(type==='dm'&&sender){openDM(sender);toggleNotifPanel();}}
function clearNotifs(){notifications=[];unreadNotifCount=0;document.getElementById("notif-count").style.display="none";renderNotifs();}
function toggleOptionsMenu(){optionsOpen=!optionsOpen;closeOtherPanels("options");document.getElementById("options-menu").classList.toggle("show",optionsOpen);document.getElementById("options-toggle").classList.toggle("active",optionsOpen);if(optionsOpen)document.getElementById("members-desc").textContent=`${onlineUsers.length} members online`;}
function closeOptionsMenu(){optionsOpen=false;document.getElementById("options-menu").classList.remove("show");document.getElementById("options-toggle").classList.remove("active");}
function toggleMuteRoom(){roomMuted=!roomMuted;document.getElementById("mute-title").textContent=roomMuted?"Unmute Room":"Mute Room";document.getElementById("mute-desc").textContent=roomMuted?"Currently muted":"Stop notifications";document.getElementById("mute-item").classList.toggle("active-opt",roomMuted);closeOptionsMenu();addNotification("system",roomMuted?"🔇 Room muted":"🔔 Room unmuted","system");}
function showPinnedMessages(){closeOptionsMenu();closeOtherPanels("pinned");document.getElementById("pinned-panel").classList.add("show");renderPinnedMessages();}
function closePinned(){document.getElementById("pinned-panel").classList.remove("show");}
function pinMessage(id,sender,text){if(pinnedMessages.find(p=>p.id===id))return;pinnedMessages.push({id,sender,text});addNotification("system","📌 Message pinned","system");}
function renderPinnedMessages(){const list=document.getElementById("pinned-list");if(pinnedMessages.length===0){list.innerHTML='<div class="notif-empty">&#128204; No pinned messages</div>';return;}list.innerHTML=pinnedMessages.map(p=>`<div class="pinned-msg-item"><div class="pinned-msg-av" style="background:${userColor(p.sender)}">${p.sender[0].toUpperCase()}</div><div class="pinned-msg-body"><div class="pinned-msg-sender">${esc(p.sender)}</div><div class="pinned-msg-text">${esc(p.text)}</div></div><button onclick="unpinMessage(${p.id})" style="background:transparent;border:none;color:var(--text-dim);cursor:pointer;font-size:.9rem;">&#10005;</button></div>`).join("");}
function unpinMessage(id){pinnedMessages=pinnedMessages.filter(p=>p.id!==id);renderPinnedMessages();}
function showRoomMembers(){closeOptionsMenu();closeOtherPanels("members");document.getElementById("members-panel").classList.add("show");renderRoomMembers();}
function closeMembers(){document.getElementById("members-panel").classList.remove("show");}
function renderRoomMembers(){const list=document.getElementById("members-list");const online=allUsers.filter(u=>onlineUsers.includes(u));const offline=allUsers.filter(u=>!onlineUsers.includes(u));let html="";if(online.length>0){html+=`<div class="members-section">Online — ${online.length}</div>`;html+=online.map(u=>`<div class="members-item" onclick="openProfile('${u}');closeMembers()"><div class="members-av" style="background:${userColor(u)}">${u[0].toUpperCase()}<div class="members-st on"></div></div><div><div class="members-name">${esc(u)}${u===myName?" (you)":""}</div><div class="members-status">Online</div></div></div>`).join("");}if(offline.length>0){html+=`<div class="members-section">Offline — ${offline.length}</div>`;html+=offline.map(u=>`<div class="members-item" onclick="openProfile('${u}');closeMembers()"><div class="members-av" style="background:${userColor(u)}">${u[0].toUpperCase()}<div class="members-st"></div></div><div><div class="members-name">${esc(u)}</div><div class="members-status">Offline</div></div></div>`).join("");}list.innerHTML=html;}
function exportChat(){closeOptionsMenu();const rows=document.querySelectorAll(".msg-row");let text=`GufGaff Export — ${document.getElementById("ch-title").textContent}\nExported: ${new Date().toLocaleString()}\n${"─".repeat(40)}\n\n`;rows.forEach(row=>{const sender=row.querySelector(".msg-name")?.textContent||"";const ts=row.querySelector(".msg-ts")?.textContent||"";const msg=row.querySelector(".msg-text")?.textContent||"";if(sender&&msg)text+=`[${ts}] ${sender}: ${msg}\n`;});const a=document.createElement("a");a.href=URL.createObjectURL(new Blob([text],{type:"text/plain"}));a.download=`gufgaff-${document.getElementById("ch-title").textContent}-${Date.now()}.txt`;a.click();}
function clearChatMessages(){if(!confirm("Clear all messages from screen?"))return;closeOptionsMenu();clearMsgs();addDateDiv("Messages cleared");}
function closeOtherPanels(except){if(except!=="search"&&searchOpen){searchOpen=false;document.getElementById("search-panel").classList.remove("show");document.getElementById("search-toggle").classList.remove("active");}if(except!=="notif"&&notifOpen){notifOpen=false;document.getElementById("notif-panel").classList.remove("show");document.getElementById("notif-toggle").classList.remove("active");}if(except!=="options"&&optionsOpen){optionsOpen=false;document.getElementById("options-menu").classList.remove("show");document.getElementById("options-toggle").classList.remove("active");}if(except!=="pinned")document.getElementById("pinned-panel").classList.remove("show");if(except!=="members")document.getElementById("members-panel").classList.remove("show");}
function toggleSearch(){searchOpen=!searchOpen;closeOtherPanels("search");document.getElementById("search-panel").classList.toggle("show",searchOpen);document.getElementById("search-toggle").classList.toggle("active",searchOpen);if(searchOpen)document.getElementById("search-input").focus();}
function doSearch(){const q=document.getElementById("search-input").value.trim();if(!q||!ws||ws.readyState!==WebSocket.OPEN)return;ws.send(JSON.stringify({type:"search",query:q}));}
function showSearchResults(results,query){const box=document.getElementById("search-results");if(results.length===0){box.innerHTML=`<div class="search-no-results">No results for "${esc(query)}"</div>`;return;}box.innerHTML=results.map(r=>`<div class="search-result-item"><div class="search-result-sender">${esc(r.sender)}</div><div class="search-result-text">${esc(r.text)}</div><div class="search-result-time">${esc(formatTs(r.timestamp))}</div></div>`).join("");}
document.getElementById("search-input").addEventListener("keydown",e=>{if(e.key==="Enter")doSearch();});
let profileUser="";
function openProfile(username){
  profileUser=username;
  const isOnline=onlineUsers.includes(username);
  const av=document.getElementById("profile-av");av.style.background=userColor(username);av.textContent=username[0].toUpperCase();
  document.getElementById("profile-name").textContent=username;
  const userData=usersData.find(u=>u.username===username);
  document.getElementById("profile-tag").textContent=userData?.is_admin?"👑 Admin":"GufGaff User";
  document.getElementById("profile-status-dot").style.background=isOnline?"var(--green)":"var(--text-dim)";
  document.getElementById("profile-status-text").textContent=isOnline?"Online":"Offline";
  const isMe=username===myName;
  document.getElementById("profile-dm-btn").style.display=isMe?"none":"block";
  document.getElementById("profile-call-btn").style.display=isMe?"none":"block";
  document.getElementById("profile-audio-btn").style.display=isMe?"none":"block";
  const adminSection=document.getElementById("profile-admin-section");
  if(amAdmin&&!isMe){
    adminSection.style.display="block";
    const isBanned=userData?.is_banned||false;const isAdm=userData?.is_admin||false;
    document.getElementById("admin-ban-btn").style.display=isBanned?"none":"block";
    document.getElementById("admin-unban-btn").style.display=isBanned?"block":"none";
    document.getElementById("admin-promote-btn").style.display=isAdm?"none":"block";
    document.getElementById("admin-demote-btn").style.display=isAdm?"block":"none";
  }else{adminSection.style.display="none";}
  document.getElementById("profile-modal").classList.add("show");
}
function openMyProfile(){openProfile(myName);}
function closeProfile(){document.getElementById("profile-modal").classList.remove("show");}
function profileSendDM(){closeProfile();openDM(profileUser);}
function buildEmojiPicker(){document.getElementById("emoji-cats").innerHTML=Object.keys(EMOJIS).map((cat,i)=>`<button class="emoji-cat-btn ${i===0?'active':''}" title="${cat}" onclick="scrollToCategory('${cat}',this)">${EMOJI_ICONS[cat]||"😀"}</button>`).join("");document.getElementById("emoji-body").innerHTML=Object.entries(EMOJIS).map(([cat,emojis])=>`<div class="emoji-section" id="cat-${cat.replace(/[\s&]/g,'-')}"><div class="emoji-category">${cat}</div><div class="emoji-grid">${emojis.map(e=>`<button class="emoji-btn" onclick="insertEmoji('${e}')">${e}</button>`).join("")}</div></div>`).join("");}
function scrollToCategory(cat,btn){document.querySelectorAll(".emoji-cat-btn").forEach(b=>b.classList.remove("active"));btn.classList.add("active");const s=document.getElementById(`cat-${cat.replace(/[\s&]/g,'-')}`);if(s)s.scrollIntoView({behavior:"smooth",block:"start"});}
function searchEmoji(val){const body=document.getElementById("emoji-body");if(!val){buildEmojiPicker();return;}const all=Object.values(EMOJIS).flat();body.innerHTML=`<div class="emoji-category">Results</div><div class="emoji-grid">${all.map(e=>`<button class="emoji-btn" onclick="insertEmoji('${e}')">${e}</button>`).join("")}</div>`;}
function toggleEmoji(){emojiOpen=!emojiOpen;document.getElementById("emoji-picker").classList.toggle("show",emojiOpen);document.getElementById("emoji-toggle").classList.toggle("active",emojiOpen);if(emojiOpen)document.querySelector(".emoji-search").focus();}
function insertEmoji(e){const input=document.getElementById("msg-input");const pos=input.selectionStart;input.value=input.value.slice(0,pos)+e+input.value.slice(pos);input.selectionStart=input.selectionEnd=pos+e.length;input.focus();}
function scrollEmoji(amount){document.getElementById("emoji-body").scrollBy({top:amount,behavior:"smooth"});}
function scrollToTop(){document.getElementById("emoji-body").scrollTo({top:0,behavior:"smooth"});}
function triggerUpload(){document.getElementById("file-input").click();}
async function uploadImage(input){if(!input.files||!input.files[0])return;const file=input.files[0];if(file.size>5*1024*1024){alert("Image too large! Max 5MB.");return;}document.getElementById("upload-progress").classList.add("show");const formData=new FormData();formData.append("file",file);try{const res=await fetch("/upload",{method:"POST",body:formData});const data=await res.json();if(data.error){alert(data.error);return;}const imageMsg=`[IMAGE]${data.url}`;if(currentChat?.type==="dm")ws.send(JSON.stringify({type:"dm",to:currentChat.id,text:imageMsg}));else ws.send(JSON.stringify({text:imageMsg}));}catch(e){alert("Upload failed.");}finally{document.getElementById("upload-progress").classList.remove("show");input.value="";}}
function openPreview(src){currentPreviewSrc=src;document.getElementById("preview-img").src=src;document.getElementById("img-preview").classList.add("show");}
function closePreview(){document.getElementById("img-preview").classList.remove("show");}
function downloadImg(){const a=document.createElement("a");a.href=currentPreviewSrc;a.download="gufgaff-image";a.click();}
document.addEventListener("paste",async e=>{if(!ws||ws.readyState!==WebSocket.OPEN||!currentChat)return;const items=e.clipboardData?.items;if(!items)return;for(const item of items){if(item.type.startsWith("image/")){const file=item.getAsFile();if(file){const dt=new DataTransfer();dt.items.add(file);document.getElementById("file-input").files=dt.files;await uploadImage(document.getElementById("file-input"));}}}});
function showTyping(name){if(typingTimers[name])clearTimeout(typingTimers[name]);typingTimers[name]=setTimeout(()=>{delete typingTimers[name];updateTypingUI();},2000);updateTypingUI();}
function updateTypingUI(){const names=Object.keys(typingTimers);const dots=document.getElementById("typing-dots");const text=document.getElementById("typing-text");if(names.length===0){dots.style.display="none";text.textContent="";}else if(names.length===1){dots.style.display="flex";text.textContent=`${names[0]} is typing...`;}else if(names.length===2){dots.style.display="flex";text.textContent=`${names[0]} and ${names[1]} are typing...`;}else{dots.style.display="flex";text.textContent="Several people are typing...";}}
function buildRooms(rooms){document.getElementById("room-list").innerHTML=rooms.map(r=>`<div class="ch-item" id="room-${r}" onclick="openRoom('${r}')"><span class="ch-hash">#</span><div class="ch-info"><div class="ch-name">${esc(r)}</div><div class="ch-desc-small">${esc(ROOM_DESC[r]||"")}</div></div>${r==="general"?'<div class="ch-dot"></div>':""}</div>`).join("");openRoom("general");}
function buildContacts(filter=""){const others=allUsers.filter(u=>u!==myName&&u.toLowerCase().includes(filter.toLowerCase()));document.getElementById("contact-list").innerHTML=others.length===0?`<div style="padding:6px 16px;font-size:.75rem;color:var(--text-dim)">No users yet</div>`:others.map(u=>{const on=onlineUsers.includes(u),unread=unreadCounts[u]||0;const ud=usersData.find(x=>x.username===u);return `<div class="dm-item" id="dm-${u}" onclick="openDM('${u}')"><div class="dm-av" style="background:${userColor(u)}" onclick="event.stopPropagation();openProfile('${u}')">${u[0].toUpperCase()}<div class="dm-st ${on?"on":""}"></div></div><div class="dm-info"><div class="dm-name">${esc(u)}${ud?.is_admin?" 👑":""}</div><div class="dm-sub">${on?"Online":"Offline"}</div></div>${unread>0?`<div class="unread-badge">${unread}</div>`:""}</div>`;}).join("");}
function filterAll(val){buildContacts(val);}
function updateCount(){document.getElementById("online-count").textContent=onlineUsers.length+" Members";}
function openRoom(room){currentChat={type:"room",id:room};polls={};setActive(`room-${room}`);document.getElementById("ch-icon").textContent="#";document.getElementById("ch-title").textContent=room;document.getElementById("ch-topic").textContent=ROOM_DESC[room]||"";document.getElementById("msg-input").placeholder=`Message #${room}`;lastSender="";lastTs="";typingTimers={};updateTypingUI();pinnedMessages=[];cancelReply();ws.send(JSON.stringify({type:"switch_room",room}));closeSidebar();}
function openDM(username){currentChat={type:"dm",id:username};unreadCounts[username]=0;setActive(`dm-${username}`);document.getElementById("ch-icon").textContent="@";document.getElementById("ch-title").textContent=username;document.getElementById("ch-topic").textContent=`Direct message with ${username}`;document.getElementById("msg-input").placeholder=`Message ${username}`;lastSender="";lastTs="";typingTimers={};updateTypingUI();clearMsgs();addDateDiv("Today");cancelReply();ws.send(JSON.stringify({type:"load_dm",with:username}));buildContacts();closeSidebar();}
function setActive(id){document.querySelectorAll(".ch-item,.dm-item").forEach(el=>el.classList.remove("active"));const el=document.getElementById(id);if(el)el.classList.add("active");}
function clearMsgs(){document.getElementById("messages").innerHTML="";lastSender="";lastTs="";polls={};}
function addDateDiv(label){const d=document.createElement("div");d.className="date-div";d.textContent=label;document.getElementById("messages").appendChild(d);}

function addMsg(id,sender,text,ts,isSelf,edited,reply_to,reply_text,reply_sender,reactions){
  const box=document.getElementById("messages");const isFirst=sender!==lastSender;lastSender=sender;
  const row=document.createElement("div");row.className=`msg-row${isFirst?" first":""}`;row.id=`msg-${id}`;
  const col=document.createElement("div");col.className="av-col";
  const av=document.createElement("div");av.className=`msg-av${!isFirst?" hidden":""}`;av.style.background=userColor(sender);av.textContent=sender[0].toUpperCase();av.onclick=()=>openProfile(sender);col.appendChild(av);
  const body=document.createElement("div");body.className="msg-body";
  if(isFirst){const head=document.createElement("div");head.className="msg-head";const nameSpan=document.createElement("span");const ud=usersData.find(x=>x.username===sender);nameSpan.className=`msg-name${isSelf?" me":""}${ud?.is_admin?" admin-name":""}`;nameSpan.textContent=sender;nameSpan.onclick=()=>openProfile(sender);const tsSpan=document.createElement("span");tsSpan.className="msg-ts";tsSpan.textContent=formatTs(ts);head.appendChild(nameSpan);head.appendChild(tsSpan);if(edited){const e=document.createElement("span");e.className="msg-edited";e.textContent=" (edited)";head.appendChild(e);}body.appendChild(head);}
  if(reply_to&&reply_text){const replyDiv=document.createElement("div");replyDiv.className="msg-reply-preview";replyDiv.innerHTML=`<div class="msg-reply-sender">↩ ${esc(reply_sender||"")}</div><div class="msg-reply-text">${esc(reply_text.startsWith("[IMAGE]")?"📷 Image":reply_text)}</div>`;replyDiv.onclick=()=>{const el=document.getElementById(`msg-${reply_to}`);if(el)el.scrollIntoView({behavior:"smooth",block:"center"});};body.appendChild(replyDiv);}
  if(text.startsWith("[IMAGE]")){const url=text.replace("[IMAGE]","");const img=document.createElement("img");img.className="msg-img";img.src=url;img.alt="image";img.onclick=()=>openPreview(url);body.appendChild(img);}
  else{const txt=document.createElement("div");txt.className="msg-text";txt.textContent=text;body.appendChild(txt);}
  const reactDiv=document.createElement("div");reactDiv.className="msg-reactions";reactDiv.innerHTML=renderReactionBadges(id,reactions,currentChat?.type==="dm"?"dm":"room");body.appendChild(reactDiv);
  row.appendChild(col);row.appendChild(body);
  const msgType=currentChat?.type==="dm"?"dm":"room";
  const canDelete=isSelf||amAdmin;const canEdit=isSelf;
  const actions=document.createElement("div");actions.className="msg-actions";
  const replyBtn=document.createElement("button");replyBtn.className="msg-action-btn reply";replyBtn.title="Reply";replyBtn.innerHTML="&#8617;";replyBtn.onclick=()=>setReply(id,sender,text.startsWith("[IMAGE]")?"📷 Image":text);actions.appendChild(replyBtn);
  const reactBtn=document.createElement("button");reactBtn.className="msg-action-btn react";reactBtn.title="React";reactBtn.innerHTML="&#128512;";reactBtn.onclick=(e)=>{e.stopPropagation();showReactionPicker(id,msgType,reactBtn);};actions.appendChild(reactBtn);
  if(isSelf&&!text.startsWith("[IMAGE]")){const pinBtn=document.createElement("button");pinBtn.className="msg-action-btn pin";pinBtn.title="Pin";pinBtn.innerHTML="&#128204;";pinBtn.onclick=()=>pinMessage(id,sender,text);actions.appendChild(pinBtn);}
  if(canEdit&&!text.startsWith("[IMAGE]")){const editBtn=document.createElement("button");editBtn.className="msg-action-btn edit";editBtn.title="Edit";editBtn.innerHTML="&#9998;";editBtn.onclick=()=>startEdit(id,text,row,body);actions.appendChild(editBtn);}
  if(canDelete){const delBtn=document.createElement("button");delBtn.className="msg-action-btn delete";delBtn.title="Delete";delBtn.innerHTML="&#128465;";delBtn.onclick=()=>deleteMessage(id,!isSelf);actions.appendChild(delBtn);}
  row.appendChild(actions);
  box.appendChild(row);box.scrollTop=box.scrollHeight;
}

function startEdit(id,originalText,row,body){const existing=row.querySelector(".msg-edit-wrap");if(existing)existing.remove();const txtEl=row.querySelector(".msg-text");if(txtEl)txtEl.style.display="none";const wrap=document.createElement("div");wrap.className="msg-edit-wrap";const input=document.createElement("input");input.className="msg-edit-input";input.value=originalText;input.type="text";const saveBtn=document.createElement("button");saveBtn.className="msg-edit-save";saveBtn.textContent="Save";const cancelBtn=document.createElement("button");cancelBtn.className="msg-edit-cancel";cancelBtn.textContent="Cancel";saveBtn.onclick=()=>{const newText=input.value.trim();if(!newText||newText===originalText){cancelEdit(row,txtEl,wrap);return;}ws.send(JSON.stringify({type:"edit_message",id,text:newText,is_dm:currentChat?.type==="dm",other:currentChat?.type==="dm"?currentChat.id:null}));cancelEdit(row,txtEl,wrap);};cancelBtn.onclick=()=>cancelEdit(row,txtEl,wrap);input.addEventListener("keydown",e=>{if(e.key==="Enter")saveBtn.click();if(e.key==="Escape")cancelBtn.click();});wrap.appendChild(input);wrap.appendChild(saveBtn);wrap.appendChild(cancelBtn);body.appendChild(wrap);input.focus();input.select();}
function cancelEdit(row,txtEl,wrap){if(txtEl)txtEl.style.display="";if(wrap&&wrap.parentNode)wrap.remove();}
function deleteMessage(id,force=false){if(!confirm("Delete this message?"))return;ws.send(JSON.stringify({type:"delete_message",id,is_dm:currentChat?.type==="dm",other:currentChat?.type==="dm"?currentChat.id:null,force}));}
function addSys(text){const d=document.createElement("div");d.className="sys-msg";d.textContent=text;document.getElementById("messages").appendChild(d);document.getElementById("messages").scrollTop=9999;addNotification("system",text,"system");}
function sendMsg(){
  const input=document.getElementById("msg-input");const text=input.value.trim();
  if(!text||!ws||ws.readyState!==WebSocket.OPEN)return;
  if(myTypingTimer){clearTimeout(myTypingTimer);myTypingTimer=null;}
  const msgData={text,reply_to:replyTo,reply_text:replyText,reply_sender:replySender};
  if(currentChat?.type==="dm")ws.send(JSON.stringify({type:"dm",to:currentChat.id,...msgData}));
  else ws.send(JSON.stringify(msgData));
  input.value="";input.focus();cancelReply();
  if(emojiOpen){emojiOpen=false;document.getElementById("emoji-picker").classList.remove("show");document.getElementById("emoji-toggle").classList.remove("active");}
}
document.getElementById("msg-input").addEventListener("keydown",e=>{if(e.key==="Enter"){e.preventDefault();sendMsg();}});
document.getElementById("auth-password").addEventListener("keydown",e=>{if(e.key==="Enter")doAuth("login");});
document.getElementById("auth-username").addEventListener("keydown",e=>{if(e.key==="Enter")doAuth("login");});
document.getElementById("msg-input").addEventListener("input",()=>{if(!ws||ws.readyState!==WebSocket.OPEN||!currentChat)return;if(myTypingTimer)clearTimeout(myTypingTimer);if(currentChat.type==="dm")ws.send(JSON.stringify({type:"typing",to:currentChat.id}));else ws.send(JSON.stringify({type:"typing",room:currentChat.id}));myTypingTimer=setTimeout(()=>{myTypingTimer=null;},1500);});
document.addEventListener("click",e=>{
  if(emojiOpen&&!e.target.closest("#emoji-picker")&&!e.target.closest("#emoji-toggle")){emojiOpen=false;document.getElementById("emoji-picker").classList.remove("show");document.getElementById("emoji-toggle").classList.remove("active");}
  if(searchOpen&&!e.target.closest("#search-panel")&&!e.target.closest("#search-toggle")){searchOpen=false;document.getElementById("search-panel").classList.remove("show");document.getElementById("search-toggle").classList.remove("active");}
  if(notifOpen&&!e.target.closest("#notif-panel")&&!e.target.closest("#notif-toggle")){notifOpen=false;document.getElementById("notif-panel").classList.remove("show");document.getElementById("notif-toggle").classList.remove("active");}
  if(optionsOpen&&!e.target.closest("#options-menu")&&!e.target.closest("#options-toggle")){optionsOpen=false;document.getElementById("options-menu").classList.remove("show");document.getElementById("options-toggle").classList.remove("active");}
});
function esc(str){return String(str).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");}
function formatTs(ts){
  if(!ts)return"";
  if(/^\d{2}:\d{2}$/.test(ts))return ts;
  const d=new Date(ts);if(isNaN(d))return ts;
  const now=new Date();
  const time=d.toLocaleTimeString([],{hour:"2-digit",minute:"2-digit"});
  if(d.toDateString()===now.toDateString())return time;
  const yest=new Date(now);yest.setDate(now.getDate()-1);
  if(d.toDateString()===yest.toDateString())return`Yesterday ${time}`;
  return`${d.toLocaleDateString([],{month:"short",day:"numeric"})} ${time}`;
}
window.addEventListener("load",()=>{
  const theme=sessionStorage.getItem("fc_theme");if(theme==="light"){isDark=false;document.body.classList.add("light");}
  const {u,p}=getSaved();if(u&&p){document.getElementById("auth-username").value=u;connectWS("login",u,p);}
});

// ── AUDIO/VIDEO CALL ──────────────────────────────
let peerConnection=null,localStream=null,callWith=null,callOffer=null,callType="video";
let micOn=true,camOn=true;
const STUN={iceServers:[
  {urls:"stun:stun.l.google.com:19302"},
  {urls:"stun:stun1.l.google.com:19302"},
  {urls:"stun:stun2.l.google.com:19302"},
  {urls:"stun:stun3.l.google.com:19302"},
  {urls:"turn:openrelay.metered.ca:80",username:"openrelayproject",credential:"openrelayproject"},
  {urls:"turn:openrelay.metered.ca:443",username:"openrelayproject",credential:"openrelayproject"},
  {urls:"turn:openrelay.metered.ca:443?transport=tcp",username:"openrelayproject",credential:"openrelayproject"}
]};

async function startCall(username,type="video"){
  if(callWith){alert("Already in a call!");return;}
  callWith=username;callType=type;
  document.getElementById("call-info-name").textContent=username;
  document.getElementById("call-info-status").textContent=type==="audio"?"Calling (Audio)...":"Calling (Video)...";
  document.getElementById("remote-label").textContent=username;
  const remoteWrap=document.querySelector(".call-video-wrap.remote");
  const localWrap=document.querySelector(".call-video-wrap.local");
  const camBtn=document.getElementById("cam-btn");
  const audioInd=document.getElementById("call-audio-indicator");
  if(type==="audio"){remoteWrap.style.display="none";localWrap.style.display="none";camBtn.style.display="none";audioInd.style.display="flex";document.getElementById("call-audio-av").textContent=username[0].toUpperCase();document.getElementById("call-audio-av").style.background=userColor(username);}
  else{remoteWrap.style.display="";localWrap.style.display="";camBtn.style.display="";audioInd.style.display="none";}
  document.getElementById("call-overlay").classList.add("show");
  try{
    const constraints=type==="audio"?{video:false,audio:true}:{video:true,audio:true};
    localStream=await navigator.mediaDevices.getUserMedia(constraints);
    if(type==="video")document.getElementById("local-video").srcObject=localStream;
    peerConnection=new RTCPeerConnection(STUN);
    localStream.getTracks().forEach(t=>peerConnection.addTrack(t,localStream));
    peerConnection.onicecandidate=e=>{if(e.candidate&&ws&&ws.readyState===WebSocket.OPEN)ws.send(JSON.stringify({type:"call_ice",to:callWith,candidate:e.candidate}));};
    peerConnection.ontrack=e=>{
      console.log("Got remote track:",e.track.kind);
      if(type==="video"){const rv=document.getElementById("remote-video");rv.srcObject=e.streams[0];rv.play().catch(err=>console.log(err));}
      else{const audio=document.getElementById("remote-audio");audio.srcObject=e.streams[0];audio.play().catch(err=>console.log(err));}
      document.getElementById("call-info-status").textContent="Connected ✅";
    };
    const offer=await peerConnection.createOffer();
    await peerConnection.setLocalDescription(offer);
    ws.send(JSON.stringify({type:"call_offer",to:username,offer,callType:type}));
  }catch(e){alert("Could not access microphone/camera: "+e.message);endCall();}
}

async function acceptCall(){
  document.getElementById("incoming-call").classList.remove("show");
  document.getElementById("call-info-name").textContent=callWith;
  document.getElementById("call-info-status").textContent="Connecting...";
  document.getElementById("remote-label").textContent=callWith;
  const remoteWrap=document.querySelector(".call-video-wrap.remote");
  const localWrap=document.querySelector(".call-video-wrap.local");
  const camBtn=document.getElementById("cam-btn");
  const audioInd=document.getElementById("call-audio-indicator");
  if(callType==="audio"){remoteWrap.style.display="none";localWrap.style.display="none";camBtn.style.display="none";audioInd.style.display="flex";document.getElementById("call-audio-av").textContent=callWith[0].toUpperCase();document.getElementById("call-audio-av").style.background=userColor(callWith);}
  else{remoteWrap.style.display="";localWrap.style.display="";camBtn.style.display="";audioInd.style.display="none";}
  document.getElementById("call-overlay").classList.add("show");
  try{
    const constraints=callType==="audio"?{video:false,audio:true}:{video:true,audio:true};
    localStream=await navigator.mediaDevices.getUserMedia(constraints);
    if(callType==="video")document.getElementById("local-video").srcObject=localStream;
    peerConnection=new RTCPeerConnection(STUN);
    localStream.getTracks().forEach(t=>peerConnection.addTrack(t,localStream));
    peerConnection.onicecandidate=e=>{if(e.candidate&&ws&&ws.readyState===WebSocket.OPEN)ws.send(JSON.stringify({type:"call_ice",to:callWith,candidate:e.candidate}));};
    peerConnection.ontrack=e=>{
      console.log("Got remote track:",e.track.kind);
      if(callType==="video"){const rv=document.getElementById("remote-video");rv.srcObject=e.streams[0];rv.play().catch(err=>console.log(err));}
      else{const audio=document.getElementById("remote-audio");audio.srcObject=e.streams[0];audio.play().catch(err=>console.log(err));}
      document.getElementById("call-info-status").textContent="Connected ✅";
    };
    await peerConnection.setRemoteDescription(new RTCSessionDescription(callOffer));
    const answer=await peerConnection.createAnswer();
    await peerConnection.setLocalDescription(answer);
    ws.send(JSON.stringify({type:"call_answer",to:callWith,answer}));
  }catch(e){alert("Could not access microphone/camera: "+e.message);endCall();}
}

function rejectCall(){document.getElementById("incoming-call").classList.remove("show");if(callWith)ws.send(JSON.stringify({type:"call_reject",to:callWith}));callWith=null;callOffer=null;}
function endCall(){if(callWith&&ws&&ws.readyState===WebSocket.OPEN)ws.send(JSON.stringify({type:"call_end",to:callWith}));cleanupCall();}
function cleanupCall(){
  if(localStream)localStream.getTracks().forEach(t=>t.stop());
  if(peerConnection)peerConnection.close();
  localStream=null;peerConnection=null;callWith=null;callOffer=null;callType="video";
  document.getElementById("call-overlay").classList.remove("show");
  document.getElementById("incoming-call").classList.remove("show");
  document.getElementById("local-video").srcObject=null;
  document.getElementById("remote-video").srcObject=null;
  const audio=document.getElementById("remote-audio");audio.srcObject=null;
  document.getElementById("call-info-status").textContent="Connecting...";
  micOn=true;camOn=true;
  document.getElementById("mute-btn").classList.remove("active");
  document.getElementById("cam-btn").classList.remove("active");
  document.querySelector(".call-video-wrap.remote").style.display="";
  document.querySelector(".call-video-wrap.local").style.display="";
  document.getElementById("cam-btn").style.display="";
  document.getElementById("call-audio-indicator").style.display="none";
}
function toggleMic(){micOn=!micOn;if(localStream)localStream.getAudioTracks().forEach(t=>t.enabled=micOn);document.getElementById("mute-btn").classList.toggle("active",!micOn);document.getElementById("mute-btn").textContent=micOn?"🎤":"🔇";}
function toggleCam(){camOn=!camOn;if(localStream)localStream.getVideoTracks().forEach(t=>t.enabled=camOn);document.getElementById("cam-btn").classList.toggle("active",!camOn);document.getElementById("cam-btn").textContent=camOn?"📷":"🚫";}
function handleCallMsg(msg){
  if(msg.type==="call_offer"){if(callWith){ws.send(JSON.stringify({type:"call_reject",to:msg.from}));return;}callWith=msg.from;callOffer=msg.offer;callType=msg.callType||"video";const av=document.getElementById("incoming-call-av");av.style.background=userColor(msg.from);av.textContent=msg.from[0].toUpperCase();document.getElementById("incoming-call-name").textContent=msg.from;document.getElementById("incoming-call-text").textContent=callType==="audio"?"🎤 Incoming audio call...":"📷 Incoming video call...";document.getElementById("incoming-call").classList.add("show");}
  else if(msg.type==="call_answer"){if(peerConnection)peerConnection.setRemoteDescription(new RTCSessionDescription(msg.answer));}
  else if(msg.type==="call_ice"){if(peerConnection&&msg.candidate)peerConnection.addIceCandidate(new RTCIceCandidate(msg.candidate));}
  else if(msg.type==="call_reject"){alert(`${msg.from} declined the call.`);cleanupCall();}
  else if(msg.type==="call_end"){alert(`${msg.from} ended the call.`);cleanupCall();}
}