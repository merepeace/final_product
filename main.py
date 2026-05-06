import subprocess
import sys
import os
import time


def run_system():
    print("=" * 70)
    print("🏭 COMPLETE WAREHOUSE MANAGEMENT SYSTEM")
    print("=" * 70)

    # Setup database first
    print("\n📦 Setting up database...")
    subprocess.run([sys.executable, 'database_setup.py'])

    print("\n🤖 Starting Warehouse Management System...")
    wms_process = subprocess.Popen([sys.executable, 'warehouse_manager.py'])

    time.sleep(2)

    print("\n🖥️ Starting Order Management GUI...")
    gui_process = subprocess.Popen([sys.executable, 'order_manager.py'])

    print("\n" + "=" * 70)
    print("✅ ALL SYSTEMS ARE RUNNING!")
    print("=" * 70)
    print("\n📋 FEATURES:")
    print("   📦 PRODUCT MANAGEMENT")
    print("   • Add/Edit/Delete products dynamically")
    print("   • Properties: Name, Model, Color, Stock, Price, Location")
    print("   • Stock level indicators (Critical/Low/Normal)")
    print("   • Search functionality")
    print("   • Double-click to edit")
    print("\n   📋 ORDER MANAGEMENT")
    print("   • Product selection from dropdown")
    print("   • Stock validation (cannot exceed available)")
    print("   • Location validation (only registered zones)")
    print("   • Priority-based ordering")
    print("   • Color-coded order status")
    print("\n   🤖 WAREHOUSE MANAGEMENT")
    print("   • 2 Virtual AGVs working in parallel")
    print("   • Automatic order assignment")
    print("   • Delivery status tracking")
    print("   • Confirmation required for completion")
    print("\n   📊 SYSTEM FEATURES")
    print("   • Real-time order updates")
    print("   • System logs")
    print("   • Stock auto-updates")
    print("\n📌 INSTRUCTIONS:")
    print("   1. Go to 'Products' tab to add/edit products")
    print("   2. Switch to 'Orders' tab to create orders")
    print("   3. Select product from dropdown")
    print("   4. Enter quantity and delivery locations")
    print("   5. Watch AGVs process orders in WMS terminal")
    print("   6. Confirm delivery when status becomes 'delivering'")
    print("\n⚠️  Close the Order Management GUI to stop the system")
    print("⚠️  Press Ctrl+C in this terminal to force stop")
    print("=" * 70)

    try:
        gui_process.wait()
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down systems...")
        wms_process.terminate()
        gui_process.terminate()
        print("✅ All systems stopped.")


if __name__ == "__main__":
    # Check if running with admin privileges (optional)
    if os.name == 'nt':  # Windows
        try:
            import ctypes

            is_admin = ctypes.windll.shell32.IsUserAnAdmin()
        except:
            is_admin = False
        if not is_admin:
            print("⚠️  Note: Running without admin privileges. This is fine for normal operation.")

    run_system()