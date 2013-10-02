package utem_horario;

import java.io.IOException;

import org.jsoup.Connection;
import org.jsoup.Connection.Method;
import org.jsoup.Connection.Response;
import org.jsoup.Jsoup;
import org.jsoup.nodes.Document;
import org.jsoup.parser.Parser;

public class Dirdoc {

	private String horario_url = "http://postulacion.utem.cl/alumnos/horario.php";
	private String alumnos_url = "http://postulacion.utem.cl/alumnos";
	private String valida = "http://postulacion.utem.cl/valida.php";
	private String user;
	private String pass;
	public Document dirdoc = null;
	public Document index = null;

	public Dirdoc(String user, String pass) {
		// TODO Auto-generated constructor stub
		this.pass = pass;
		this.user = user;

		// establecer una sesion de alumno de dirdoc (Log in)

		Response res = null;
		try {
			res = Jsoup.connect(this.valida).data("rut", this.user)
					.data("password", this.pass).data("tipo", "0")
					.method(Method.POST).execute();
		} catch (IOException e1) {
			// TODO Auto-generated catch block
			e1.printStackTrace();
		}

		// parsear las paginas necesarias
		try {
			index = Jsoup
					.connect("http://postulacion.utem.cl/alumnos/index.php")
					.cookies(res.cookies()).get();

		} catch (Exception e) {
			System.out.println("nos fuimos a la B " + e);
		}

	}

}
