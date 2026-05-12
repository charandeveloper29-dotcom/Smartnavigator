/* Smart Navigator - main.js */
(function(){
  const navbar=document.getElementById("navbar");
  const hamburger=document.getElementById("hamburger");
  const navLinks=document.getElementById("navLinks");
  if(navbar){window.addEventListener("scroll",()=>{navbar.classList.toggle("scrolled",window.scrollY>20);},{passive:true});}
  if(hamburger&&navLinks){hamburger.addEventListener("click",()=>{navLinks.classList.toggle("open");});document.addEventListener("click",e=>{if(!e.target.closest("#navbar"))navLinks.classList.remove("open");});}
  document.addEventListener("click",e=>{if(!e.target.closest("#navLangSwitcher")){const dd=document.getElementById("langDropdown");if(dd)dd.hidden=true;}});
})();

async function apiFetch(url,options={}){
  try{const res=await fetch(url,{headers:{"Content-Type":"application/json"},credentials:"same-origin",...options});const data=await res.json();return{ok:res.ok,status:res.status,data};}
  catch(err){return{ok:false,status:0,data:{error:"Network error"}};}
}

async function toggleSave(placeId,btn){
  const{ok,data}=await apiFetch("/api/places/"+placeId+"/save",{method:"POST"});
  if(!ok){if(data.code===401||String(data.error).includes("Authentication")){window.location.href="/login";}return;}
  const saved=data.action==="saved";
  btn.textContent=saved?"❤️":"🤍";
  btn.classList.toggle("saved",saved);
  if(btn.id==="heroSaveBtn")btn.innerHTML=saved?"❤️ Saved":"🤍 Save Place";
}

function initStarInput(){
  const stars=document.querySelectorAll(".star-pick");
  const input=document.getElementById("reviewRating");
  if(!stars.length||!input)return;
  stars.forEach(star=>{
    star.addEventListener("mouseover",()=>hl(stars,+star.dataset.val));
    star.addEventListener("mouseout",()=>hl(stars,+input.value));
    star.addEventListener("click",()=>{input.value=star.dataset.val;hl(stars,+star.dataset.val);});
  });
}
function hl(stars,val){stars.forEach(s=>s.classList.toggle("active",+s.dataset.val<=val));}

async function submitReview(placeId){
  const rating=+document.getElementById("reviewRating").value;
  const title=document.getElementById("reviewTitle").value.trim();
  const content=document.getElementById("reviewContent").value.trim();
  const msgEl=document.getElementById("reviewMsg");
  if(!rating){showMsg(msgEl,"Please select a star rating.","error");return;}
  if(!title){showMsg(msgEl,"Please enter a title.","error");return;}
  if(content.length<10){showMsg(msgEl,"Review must be at least 10 characters.","error");return;}
  const{ok,data}=await apiFetch("/api/places/"+placeId+"/reviews",{method:"POST",body:JSON.stringify({rating,title,content})});
  if(ok){showMsg(msgEl,"Review submitted! Thank you.","success");const list=document.getElementById("reviewsList");if(list)list.insertAdjacentHTML("afterbegin",buildRevCard(data.review));document.getElementById("reviewTitle").value="";document.getElementById("reviewContent").value="";document.getElementById("reviewRating").value="0";hl(document.querySelectorAll(".star-pick"),0);}
  else{showMsg(msgEl,data.error||"Could not submit review.","error");}
}

function buildRevCard(r){
  const stars=[1,2,3,4,5].map(i=>"<span class="star "+(i<=r.rating?"filled":"")+"">★</span>").join("");
  return "<div class="review-card"><div class="review-header"><div class="reviewer-avatar">"+(r.user_name||"?")[0].toUpperCase()+"</div><div><span class="reviewer-name">"+escHtml(r.user_name)+"</span><span class="review-date">"+r.created_at.slice(0,10)+"</span></div><div class="review-stars">"+stars+"</div></div><h4 class="review-title">"+escHtml(r.title)+"</h4><p class="review-content">"+escHtml(r.content)+"</p></div>";
}

function initModeTabs(){
  const tabs=document.querySelectorAll(".mode-tab");
  const cards=document.querySelectorAll(".route-card");
  if(!tabs.length)return;
  tabs.forEach(tab=>{tab.addEventListener("click",()=>{tabs.forEach(t=>t.classList.remove("active"));tab.classList.add("active");const mode=tab.dataset.mode;cards.forEach(c=>{c.classList.toggle("hidden",mode!=="all"&&c.dataset.mode!==mode);});});});
}

function showMsg(el,msg,type){if(!el)return;el.textContent=msg;el.className="review-msg "+type;}
function escHtml(str){return String(str).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");}

const CAT_ICONS={heritage:"🏛️",nature:"🌿",beach:"🏖️",hill:"⛰️",city:"🏙️"};

document.addEventListener("DOMContentLoaded",()=>{
  initStarInput();
  initModeTabs();
  const lang=localStorage.getItem("sn_lang")||"en";
  if(typeof applyTranslation==="function")applyTranslation(lang);
});
