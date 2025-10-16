// frontend/src/components/common/Footer.jsx
import './Footer.css';

function Footer() {
  return (
    <footer className="app-footer">
      <div className="footer-content">
        {/* ✨ 加上 className="footer-group" 和 "lab-info" */}
        <div className="footer-group lab-info">
          <span className="lab-name">人工智慧與知識系統實驗室</span>
          <span className="lab-name-en">Artificial Intelligence & Knowledge System Lab</span>
        </div>

        <div className="footer-separator"></div>

        {/* ✨ 加上 className="footer-group" 和 "credits" */}
        <div className="footer-group credits">
          <span className="credit-line">開發者：陳淳瑜、陳玟樺、劉品媛</span>
          <span className="credit-line">指導教授：楊鎮華 教授</span>
        </div>

        <div className="footer-separator"></div>

        {/* ✨ 加上 className="footer-group" 和 "contact-info" */}
        <div className="footer-group contact-info">
            <span className="contact-line">地址：(320317) 桃園市中壢區中大路300號 國立中央大學工程五館 E6-B320</span>
            <span className="contact-line">Tel：03 - 4227151 分機 : 35353</span>
        </div>
      </div>
    </footer>
  );
}

export default Footer;