def device_tcp_url(my_ip_address: str, default_tcp_scpi_port: int) -> str:
    return f"TCPIP::{my_ip_address}::{default_tcp_scpi_port}::SOCKET"


def device_usb_url(id_vendor: int, id_product: int, my_serial_nr: str) -> str:
    return f"USB::0x{id_vendor:x}::0x{id_product:x}::{my_serial_nr}::INSTR"
